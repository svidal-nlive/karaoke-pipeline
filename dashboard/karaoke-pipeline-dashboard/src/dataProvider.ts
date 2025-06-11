// src/dataProvider.ts
import { DataProvider, RaRecord, Identifier, UpdateParams, UpdateResult } from 'react-admin';
import axios, { AxiosResponse } from 'axios';

const API_URL = process.env.REACT_APP_STATUS_API_URL || 'http://localhost:3000';

const dataProvider: DataProvider = {
  getList: async <RecordType extends RaRecord<Identifier> = any>(
    resource: string,
    params: any
  ): Promise<{ data: RecordType[]; total: number }> => {
    const response = await axios.get(`${API_URL}/${resource}`, {
      params: {
        _page: params.pagination?.page,
        _limit: params.pagination?.perPage,
        _sort: params.sort?.field,
        _order: params.sort?.order,
        ...(params.filter || {}),
      },
    });

    // Explicitly cast as RecordType[] for TypeScript
    return {
      data: response.data as RecordType[],
      total:
        typeof response.headers['x-total-count'] !== 'undefined'
          ? parseInt(response.headers['x-total-count'], 10)
          : (response.data.length || 0),
    };
  },

  getOne: async (resource, params) => {
    const { data } = await axios.get(`${API_URL}/${resource}/${params.id}`);
    return { data };
  },

  getMany: async (resource, params) => {
    const response = await axios.get(`${API_URL}/${resource}`, {
      params: { id: params.ids },
    });
    return { data: response.data };
  },

  getManyReference: async <RecordType extends RaRecord<Identifier> = any>(
    resource: string,
    params: any
  ): Promise<{ data: RecordType[]; total: number }> => {
    // Many reference is usually a filter on a foreign key, often params.target/params.id.
    const { target, id } = params;
    const response = await axios.get(`${API_URL}/${resource}`, {
      params: {
        ...params.pagination,
        ...params.sort,
        ...params.filter,
        [target]: id, // e.g. post_id: 123
      },
    });
    return {
      data: response.data as RecordType[],
      total:
        typeof response.headers['x-total-count'] !== 'undefined'
          ? parseInt(response.headers['x-total-count'], 10)
          : (response.data.length || 0),
    };
  },

  update: async <RecordType extends RaRecord = RaRecord>(
    resource: string,
    params: UpdateParams<RecordType>
  ): Promise<UpdateResult<RecordType>> => {
    // Option A: If the server returns the full record:
    const response: AxiosResponse<RecordType> = await axios.patch(
      `${API_URL}/${resource}/${params.id}`,
      params.data
    );
    return { data: response.data };

    // Option B: If the server responds with only { id }, uncomment below:
    /*
    await axios.patch(`${API_URL}/${resource}/${params.id}`, params.data);
    const { data: fresh } = await axios.get<RecordType>(`${API_URL}/${resource}/${params.id}`);
    return { data: fresh };
    */
  },

  updateMany: async (resource, params) => {
    const updated = await Promise.all(
      params.ids.map(id =>
        axios.patch(`${API_URL}/${resource}/${id}`, params.data).then(res => res.data.id)
      )
    );
    return { data: updated };
  },

  create: async (resource, params) => {
    const { data } = await axios.post(`${API_URL}/${resource}`, params.data);
    return { data };
  },

  delete: async (resource, params) => {
    const { data } = await axios.delete(`${API_URL}/${resource}/${params.id}`);
    return { data };
  },

  deleteMany: async (resource, params) => {
    await Promise.all(params.ids.map(id => axios.delete(`${API_URL}/${resource}/${id}`)));
    return { data: params.ids };
  },
};

export default dataProvider;
