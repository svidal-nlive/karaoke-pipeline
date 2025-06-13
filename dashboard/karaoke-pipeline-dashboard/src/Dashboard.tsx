import * as React from "react";
import { Card, CardContent, Typography, Box, Button, LinearProgress, Stack } from "@mui/material";
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { useNotify, useRefresh, useDataProvider, List, Datagrid, TextField, FunctionField, RaRecord } from "react-admin";

export const PipelineDashboard = () => {
  // (For future: get stats from API)
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Karaoke Pipeline Dashboard
      </Typography>
      <StatsBar />
      <Box sx={{ mt: 4 }}>
        <FileUploader />
      </Box>
    </Box>
  );
};

function StatsBar() {
  // Replace with API stats if you like
  // Example: Fetch /stats from backend
  const stats = { inProgress: 0, completed: 0, errors: 0 };
  return (
    <Stack direction="row" spacing={4}>
      <Card>
        <CardContent>
          <Typography color="text.secondary">In Progress</Typography>
          <Typography variant="h5">{stats.inProgress}</Typography>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <Typography color="text.secondary">Completed</Typography>
          <Typography variant="h5">{stats.completed}</Typography>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <Typography color="text.secondary">Errors</Typography>
          <Typography variant="h5">{stats.errors}</Typography>
        </CardContent>
      </Card>
    </Stack>
  );
}

// ---------- File Upload Component ----------

export function FileUploader() {
  const [uploading, setUploading] = React.useState(false);
  const [progress, setProgress] = React.useState(0);
  const fileInput = React.useRef<HTMLInputElement>(null);
  const notify = useNotify();
  const refresh = useRefresh();
  const uploadUrl = process.env.REACT_APP_STATUS_API_URL || "http://vectorhost.net:5001";

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const req = new XMLHttpRequest();
      req.open("POST", `${uploadUrl}/input`);
      req.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          setProgress(Math.round((event.loaded / event.total) * 100));
        }
      };
      req.onload = () => {
        setUploading(false);
        if (req.status >= 200 && req.status < 300) {
          notify("Upload successful!", { type: "info" });
          refresh();
        } else {
          notify(`Upload failed with status ${req.status}`, { type: "error" });
        }
      };
      req.onerror = () => {
        setUploading(false);
        notify("Upload failed: Network error", { type: "error" });
      };
      req.send(formData);
    } catch (err: any) {
      setUploading(false);
      notify(`Upload failed: ${err.message}`, { type: "error" });
    }
  };

  return (
    <Card sx={{ maxWidth: 400 }}>
      <CardContent>
        <Button
          variant="contained"
          component="label"
          startIcon={<CloudUploadIcon />}
          disabled={uploading}
        >
          Upload File
          <input
            type="file"
            hidden
            ref={fileInput}
            onChange={handleFileChange}
            disabled={uploading}
          />
        </Button>
        {uploading && (
          <Box sx={{ width: '100%', mt: 2 }}>
            <LinearProgress variant="determinate" value={progress} />
            <Typography variant="caption">{progress}%</Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

// ---------- File List/Datagrid ----------

export const FileList = () => (
  <List resource="files" perPage={50} title="Pipeline Files">
    <Datagrid>
      <TextField source="filename" />
      <TextField source="status" />
      <FunctionField
        label="Stages"
        render={(record: any) =>
          Object.keys(record.stages || {}).join(", ")
        }
      />
      <TextField source="last_error" />
      <RetryButton />
    </Datagrid>
  </List>
);

export const ErrorList = () => (
  <List resource="error-files" perPage={50} title="Error Files">
    <Datagrid>
      <TextField source="filename" />
      <TextField source="status" />
      <TextField source="last_error" />
      <RetryButton />
    </Datagrid>
  </List>
);

const RetryButton = () => {
  const notify = useNotify();
  const refresh = useRefresh();
  const dataProvider = useDataProvider();
  return (
    <FunctionField
      label="Retry"
      render={(record: RaRecord) =>
        <Button
          variant="outlined"
          size="small"
          onClick={async () => {
            try {
              await dataProvider.create('retry', { data: { filename: record.filename } });
              notify('Retry triggered for ' + record.filename, { type: 'info' });
              refresh();
            } catch (err: any) {
              notify('Retry failed: ' + (err && err.message), { type: 'error' });
            }
          }}
          disabled={record.status !== "error"}
        >
          Retry
        </Button>
      }
    />
  );
};
