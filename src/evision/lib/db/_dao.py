# -*- coding: utf-8 -*-
#
# Copyright 2018 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-06-12 19:54
# @version: 1.0
#
from datetime import datetime

import peewee

from evision.lib.db import ModelIsNone, ModelOfWrongType
from evision.lib.log import LogHandlers, logutil

logger = logutil.get_logger(LogHandlers.DEFAULT)

__all__ = [
    'BaseDao'
]


def _db_time_convert(info_map):
    return datetime.strptime(info_map['updated_at'], '%Y-%m-%d %H:%M:%S')


class BaseDao(object):
    model = None
    # record map should be explicitly reloaded when dataset is updated
    _record_map = {}

    def __init__(self, _model):
        self.model = _model
        self.__check_model()
        self._db = self.model._meta.database
        self._model_name = self.model._meta.table_name
        self._record_map = {}

    @property
    def primary_key_field(self):
        try:
            return self.model._meta.primary_key.name
        except Exception as e:
            logger.exception('No primary key specified for model={}: {}',
                             self._model_name, e)

    def __check_model(self):
        """ Validating the model
        """
        if self.model is None:
            raise ModelIsNone()
        if not issubclass(self.model, peewee.Model):
            raise ModelOfWrongType(type(self.model))

    def insert(self, info_map):
        """ Insert record with provided information

        :param info_map: record information
        """
        self.__check_model()

        try:
            instance = self.model(**info_map)
            row_id = instance.save(force_insert=True)
            if row_id < 0:
                raise Exception('No rows affected')
            logger.info('Model[{}] inserted, id={}, data={}',
                        self._model_name, row_id, info_map)
        except Exception as e:
            logger.exception('Failed inserting model[{}]: {}', self._model_name, e)

    @staticmethod
    def __get_update_time(update_time=None, get=False, info_map=None):
        """获取记录更新时间"""
        if info_map is None:
            info_map = {}
        if get:
            cur = _db_time_convert(info_map)
            if update_time is None or update_time < cur:
                return cur
        return update_time

    def batch_insert(self, info_map_list,
                     update_time=None, get_update_time=False):
        if not info_map_list:
            return
        self.__check_model()

        with self._db.atomic():
            for info_map in info_map_list:
                self.model(**info_map).save(force_insert=True)
                update_time = BaseDao.__get_update_time(
                    update_time, get_update_time, info_map)
        self._db.commit()
        logger.info('Insert {} records for model={}',
                    len(info_map_list), self._model_name)

        return True, update_time

    def batch_replace(self, info_map_list,
                      changed=False, update_time=None, get_update_time=True):
        """ Insert or updated multiple records

        :param info_map_list: record info list
        :param changed: whether updated
        :param update_time: update time
        :param get_update_time: whether return update time
        :return: changed, update_time
        """
        if not info_map_list:
            return changed, update_time

        self.__check_model()

        with self._db.atomic():
            for info_map in info_map_list:
                try:
                    changed = True
                    try:
                        exist_model = self.model.get_by_id(info_map[self.primary_key_field])
                    except peewee.DoesNotExist:
                        exist_model = None
                    ret = self.model(**info_map).save(force_insert=exist_model is None)
                    logger.info('Affect {} rows with info_map={}, model={}',
                                ret, info_map, self._model_name)
                    update_time = BaseDao.__get_update_time(
                        update_time, get_update_time, info_map)
                except Exception as e:
                    logger.exception('Failed create/update model[{}]={}: {}',
                                     self._model_name, info_map, e)
            self._db.commit()

        return changed, update_time

    def delete_by_id(self, id_):
        """ Delete record by id

        :param id_: record id
        """
        self.__check_model()

        try:
            deleted = self.model.delete_by_id(id_)
            logger.info('Deleted {} model[{}] by id={}',
                        deleted, self._model_name, id_)
            return deleted
        except Exception as e:
            logger.exception('Failed deleting model[{}] by id={}: {}',
                             self._model_name, id_, e)
            return -1

    def get_by_id(self, id_):
        self.__check_model()

        return self.records.get(id_, None)

    def batch_delete(self, info_map_list,
                     changed=False, update_time=None, get_update_time=True):
        """ Delete provided multiple records

        According to ids of provided records

        :param info_map_list: provided records
        :param changed: whether updated
        :param update_time: update time
        :param get_update_time: whether return update time
        :return: changed, update_time
        """
        if not info_map_list:
            return changed, update_time

        self.__check_model()
        key_field = self.primary_key_field

        with self._db.atomic():
            for info_map in info_map_list:
                try:
                    changed = True
                    self.model.delete_by_id(info_map[key_field])
                    update_time = BaseDao.__get_update_time(
                        update_time, get_update_time, info_map)
                except Exception as e:
                    logger.exception(
                        'Failed deleting model[{}]={} by id field={}: {}',
                        self._model_name, info_map, key_field, e)
            logger.info('Delete {} records for model={}',
                        len(info_map_list), self._model_name)

        return changed, update_time

    def batch_delete_with_ids(self, ids):
        """ Delete multiple records with id list

        Id of current model should be a AutoField

        :param ids: is list
        :return: number of deleted records or -1 for failing
        """
        if not ids:
            return 0
        num_model = len(ids)

        try:
            num_deleted = 0
            with self._db.atomic():
                for id_ in ids:
                    id_deleted = self.delete_by_id(id_)
                    if id_deleted > 0:
                        num_deleted += id_deleted
            logger.info('[{}] Delete {} records for {} provided',
                        self._model_name, num_deleted, num_model)
            return num_deleted
        except Exception as e:
            logger.exception('Failed deleting {} records: {}', num_model, e)
            return -1

    @property
    def records(self):
        """获取当前表所有记录"""
        if not self._record_map:
            self.reload()
        return self._record_map

    def __reload_record_map(self, record_map):
        self._record_map.clear()
        self._record_map.update(record_map)

    def reload(self):
        """ Load all records to memory
        """
        record_map = {getattr(_, self.primary_key_field): _ for _ in self.model.select()}
        self.__reload_record_map(record_map)

    @classmethod
    def raw_sql(cls, query):
        sql, params = query.sql()
        raw_sql = sql.replace('?', "'{}'").format(*params)
        return raw_sql
