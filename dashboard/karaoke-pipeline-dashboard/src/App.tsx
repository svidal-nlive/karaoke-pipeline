import * as React from "react";
import { Admin, Resource, CustomRoutes } from "react-admin";
import simpleRestProvider from "ra-data-simple-rest";
import { FileList, ErrorList, PipelineDashboard } from "./Dashboard";
import { Route } from "react-router";
import UploadFileIcon from '@mui/icons-material/UploadFile';

// Fallback URL to vectorhost.net if env var missing
const apiUrl = process.env.REACT_APP_STATUS_API_URL || "https://vectorhost.net:5001";
const dataProvider = simpleRestProvider(apiUrl);

const App = () => (
  <Admin
    dataProvider={dataProvider}
    dashboard={PipelineDashboard}
    title="Karaoke Pipeline Dashboard"
  >
    <Resource
      name="files"
      list={FileList}
      options={{ label: "All Files" }}
      icon={UploadFileIcon}
    />
    <Resource
      name="error-files"
      list={ErrorList}
      options={{ label: "Error Files" }}
    />
    <CustomRoutes>
      {/* Uncomment if dedicated upload page desired */}
      {/* <Route path="/upload" element={<FileUploader />} /> */}
    </CustomRoutes>
  </Admin>
);

export default App;
