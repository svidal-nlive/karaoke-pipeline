import * as React from "react";
import { Admin, Resource } from "react-admin";
import simpleRestProvider from "ra-data-simple-rest";
import { FileList, ErrorList } from "./Dashboard";

// Reads from .env: REACT_APP_STATUS_API_URL (docker-compose sets this)
const apiUrl = process.env.REACT_APP_STATUS_API_URL || "http://localhost:5001";
const dataProvider = simpleRestProvider(apiUrl);

const App = () => (
  <Admin dataProvider={dataProvider}>
    <Resource name="files" list={FileList} options={{ label: "All Files" }} />
    <Resource name="error-files" list={ErrorList} options={{ label: "Error Files" }} />
  </Admin>
);

export default App;
