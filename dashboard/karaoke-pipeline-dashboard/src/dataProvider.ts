// src/dataProvider.ts
import simpleRestProvider from 'ra-data-simple-rest';

const apiUrl = process.env.REACT_APP_STATUS_API_URL!;
export default simpleRestProvider(apiUrl);
