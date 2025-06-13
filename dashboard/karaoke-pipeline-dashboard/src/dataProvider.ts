// src/dataProvider.ts
import { DataProvider, RaRecord, Identifier, UpdateParams, UpdateResult } from 'react-admin';
import axios, { AxiosResponse } from 'axios';

const API_URL = process.env.REACT_APP_STATUS_API_URL || 'https://vectorhost.net:5001';

const resourceMap: Record<string, string> = {
  files: 'status',
  'error-files': 'error-files',
};

const dataProvider: DataProvider = {
  getList: async <RecordType extends RaRecord<Identifier> = any>(
    resource: string,
    params: any
  ): Promise<{ data: RecordType[]; total: number }> => {
    const apiResource = resourceMap[resource] || resource;

    // Backend does not support pagination, sorting, filtering yet
    const response = await axios.get(`${API_URL}/${apiResource}`);

    // Map filename to id for react-admin compatibility
    const data = response.data[apiResource === 'status' ? 'files' : apiResource] || response.data;
    const items: any[] = Array.isArray(data) ? data : Object.values(data);
    const mapped = items.map(item => ({
      id: item.filename || item.id || item,
      ...item,
    }));

    return {
      data: mapped as RecordType[],
      total: mapped.length,
    };
  },

  getOne: async (resource, params) => {
    const apiResource = resourceMap[resource] || resource;
    const { data } = await axios.get(`${API_URL}/${apiResource}/${params.id}`);
    return { data };
  },

  getMany: async (resource, params) => {
    const apiResource = resourceMap[resource] || resource;
    const response = await axios.get(`${API_URL}/${apiResource}`, {
      params: { id: params.ids },
    });
    return { data: response.data };
  },

  getManyReference: async <RecordType extends RaRecord<Identifier> = any>(
    resource: string,
    params: any
  ): Promise<{ data: RecordType[]; total: number }> => {
    const apiResource = resourceMap[resource] || resource;
    const { target, id } = params;
    const response = await axios.get(`${API_URL}/${apiResource}`, {
      params: {
        [target]: id,
      },
    });
    const data = response.data;
    const items: any[] = Array.isArray(data) ? data : Object.values(data);
    return {
      data: items as RecordType[],
      total: items.length,
    };
  },

  update: async <RecordType extends RaRecord = RaRecord>(
    resource: string,
    params: UpdateParams<RecordType>
  ): Promise<UpdateResult<RecordType>> => {
    const apiResource = resourceMap[resource] || resource;
    const response: AxiosResponse<RecordType> = await axios.patch(
      `${API_URL}/${apiResource}/${params.id}`,
      params.data
    );
    return { data: response.data };
  },

  updateMany: async (resource, params) => {
    const apiResource = resourceMap[resource] || resource;
    const updated = await Promise.all(
      params.ids.map(id =>
        axios.patch(`${API_URL}/${apiResource}/${id}`, params.data).then(res => res.data.id)
      )
    );
    return { data: updated };
  },

  create: async (resource, params) => {
    const apiResource = resourceMap[resource] || resource;
    const { data } = await axios.post(`${API_URL}/${apiResource}`, params.data);
    return { data };
  },

  delete: async (resource, params) => {
    const apiResource = resourceMap[resource] || resource;
    const { data } = await axios.delete(`${API_URL}/${apiResource}/${params.id}`);
    return { data };
  },

  deleteMany: async (resource, params) => {
    const apiResource = resourceMap[resource] || resource;
    await Promise.all(params.ids.map(id => axios.delete(`${API_URL}/${apiResource}/${id}`)));
    return { data: params.ids };
  },
};

export default dataProvider;
