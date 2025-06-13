// src/Dashboard.tsx
import * as React from 'react';
import {
  Admin,
  Resource,
  List,
  Datagrid,
  TextField,
  FunctionField,
  useNotify,
  useRefresh,
} from 'react-admin';
import simpleRestProvider from 'ra-data-simple-rest';
import { Card, CardContent, Typography, Box, Button, LinearProgress, Stack } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import UploadFileIcon from '@mui/icons-material/UploadFile';

// ----------------------------------------------------------------
// Dashboard (main landing page)
// ----------------------------------------------------------------
export const PipelineDashboard = () => (
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

// ----------------------------------------------------------------
// Stats Bar: fetches /pipeline-health
// ----------------------------------------------------------------
function StatsBar() {
  const [stats, setStats] = React.useState<{ queued: number; organized: number; error: number } | null>(null);

  React.useEffect(() => {
    fetch(`${process.env.REACT_APP_STATUS_API_URL}/pipeline-health`)
      .then((res) => res.json())
      .then((json) =>
        setStats({
          queued: json.queued ?? 0,
          organized: json.organized ?? 0,
          error: json.error ?? 0,
        })
      )
      .catch(() => setStats({ queued: 0, organized: 0, error: 0 }));
  }, []);

  if (!stats) return <LinearProgress sx={{ mb: 2 }} />;

  return (
    <Stack direction="row" spacing={4}>
      <Card>
        <CardContent>
          <Typography color="text.secondary">In Progress</Typography>
          <Typography variant="h5">{stats.queued}</Typography>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <Typography color="text.secondary">Completed</Typography>
          <Typography variant="h5">{stats.organized}</Typography>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <Typography color="text.secondary">Errors</Typography>
          <Typography variant="h5">{stats.error}</Typography>
        </CardContent>
      </Card>
    </Stack>
  );
}

// ----------------------------------------------------------------
// File Upload Component
// ----------------------------------------------------------------
export function FileUploader() {
  const [uploading, setUploading] = React.useState(false);
  const [progress, setProgress] = React.useState(0);
  const notify = useNotify();
  const refresh = useRefresh();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    const file = e.target.files[0];
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    const req = new XMLHttpRequest();
    req.open('POST', `${process.env.REACT_APP_STATUS_API_URL}/input`);
    req.upload.onprogress = (ev) => {
      if (ev.lengthComputable) setProgress(Math.round((ev.loaded / ev.total) * 100));
    };
    req.onload = () => {
      setUploading(false);
      if (req.status < 400) {
        notify('Upload successful!', { type: 'info' });
        refresh();
      } else {
        notify('Upload failed', { type: 'error' });
      }
    };
    req.onerror = () => {
      setUploading(false);
      notify('Upload failed', { type: 'error' });
    };
    req.send(formData);
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
          <input type="file" hidden onChange={handleFileChange} disabled={uploading} />
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

// ----------------------------------------------------------------
// File List (All Files)
// ----------------------------------------------------------------
export const FileList = (props: any) => (
  <List {...props} pagination={false} resource="status" title="All Files">
    <Datagrid rowClick="edit">
      <TextField source="filename" />
      <TextField source="status" />
      <FunctionField
        label="Stages"
        render={(record: any) => Object.keys(record.stages || {}).join(', ')}
      />
      <TextField source="last_error" />
    </Datagrid>
  </List>
);

// ----------------------------------------------------------------
// Error Files List
// ----------------------------------------------------------------
export const ErrorList = (props: any) => {
  const notify = useNotify();
  const refresh = useRefresh();

  return (
    <List {...props} pagination={false} resource="error-files" title="Error Files">
      <Datagrid>
        <TextField source="filename" />
        <TextField source="status" />
        <TextField source="last_error" />
        <FunctionField
          label="Retry"
          render={(record: any) => (
            <Button
              variant="outlined"
              size="small"
              disabled={record.status !== 'error'}
              onClick={async () => {
                try {
                  await fetch(
                    `${process.env.REACT_APP_STATUS_API_URL}/retry`,
                    {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ filename: record.filename }),
                    }
                  );
                  notify('Retry triggered for ' + record.filename, { type: 'info' });
                  refresh();
                } catch {
                  notify('Retry failed', { type: 'error' });
                }
              }}
            >
              Retry
            </Button>
          )}
        />
      </Datagrid>
    </List>
  );
};

// ----------------------------------------------------------------
// App Entry Point
// ----------------------------------------------------------------
const dataProvider = simpleRestProvider(process.env.REACT_APP_STATUS_API_URL!);

const App = () => (
  <Admin dataProvider={dataProvider} dashboard={PipelineDashboard} title="Karaoke Pipeline Dashboard">
    <Resource name="status" list={FileList} icon={UploadFileIcon} options={{ label: 'All Files' }} />
    <Resource name="error-files" list={ErrorList} options={{ label: 'Error Files' }} />
  </Admin>
);

export default App;
