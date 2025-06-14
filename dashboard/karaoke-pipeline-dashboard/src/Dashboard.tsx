// src/Dashboard.tsx
import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import {
  List,
  Datagrid,
  TextField,
  FunctionField,
  TopToolbar,
  CreateButton,
  // RefreshButton,
  Title,
  useRefresh,
} from 'react-admin';
import { Button } from '@mui/material';
import PublishIcon from '@mui/icons-material/Publish';

// --- Main Dashboard Section with Metrics ---
export const PipelineDashboard = () => {
  const refresh = useRefresh();
  const [metrics, setMetrics] = useState<any>({});
  const [sseError, setSseError] = useState(false);

  // Fetch /pipeline-health on mount and refresh
  const fetchMetrics = useCallback(() => {
    fetch(`${process.env.REACT_APP_STATUS_API_URL}/pipeline-health`)
      .then(res => res.json())
      .then(setMetrics)
      .catch(console.error);
  }, []);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // Subscribe SSE
  useEffect(() => {
    const es = new EventSource(`${process.env.REACT_APP_STATUS_API_URL}/stream`);
    es.onerror = () => setSseError(true);

    // On any event, refetch both list and metrics
    const handleEvent = () => {
      refresh();
      fetchMetrics();
    };

    // Subscribe to all stream types
    ['queued','metadata','split','packaged','organized','error'].forEach(evt =>
      es.addEventListener(`stream:${evt}`, handleEvent)
    );

    return () => {
      es.close();
    };
  }, [refresh, fetchMetrics]);

  const MyActions = () => (
    <TopToolbar>
      <CreateButton label="Upload" />
      <Button
        color="primary"
        startIcon={<PublishIcon />}
        onClick={() => refresh()}
      >
        Manual Refresh
      </Button>
    </TopToolbar>
  );

  return (
    <div style={{ padding: '1em' }}>
      <Title title="Karaoke Pipeline Dashboard" />
      <section style={{ marginBottom: '2em' }}>
        <h2>Pipeline Metrics</h2>
        <ul>
          <li>Queued: {metrics.queued ?? '-'}</li>
          <li>Metadata Extracted: {metrics.metadata_extracted ?? '-'}</li>
          <li>Split: {metrics.split ?? '-'}</li>
          <li>Packaged: {metrics.packaged ?? '-'}</li>
          <li>Organized: {metrics.organized ?? '-'}</li>
          <li>Error: {metrics.error ?? '-'}</li>
        </ul>
        {sseError && <p style={{color:'red'}}>Real-time feed disconnected</p>}
      </section>

      <List
        resource="status"
        actions={<MyActions />}
        title="All Files"
        perPage={25}
      >
        <Datagrid rowClick="edit">
          <TextField source="filename" />
          <TextField source="status" />
          <FunctionField
            label="Last Error"
            render={record => record.last_error || '—'}
          />
          <FunctionField
            label="Actions"
            render={record => (
              <Button
                onClick={() =>
                  fetch(`${process.env.REACT_APP_STATUS_API_URL}/retry`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: record.filename }),
                  }).then(() => refresh())
                }
                size="small"
              >
                Retry
              </Button>
            )}
          />
        </Datagrid>
      </List>
    </div>
  );
};

// --- List of All Files (react-admin Resource) ---
export const FileList = () => (
  <List resource="status" title="All Files" perPage={25}>
    <Datagrid>
      <TextField source="filename" />
      <TextField source="status" />
      <FunctionField
        label="Last Error"
        render={record => record.last_error || '—'}
      />
    </Datagrid>
  </List>
);

// --- List of Error Files (react-admin Resource) ---
export const ErrorList = () => (
  <List resource="error-files" title="Error Files" perPage={25}>
    <Datagrid>
      <TextField source="filename" />
      <TextField source="status" />
      <FunctionField
        label="Last Error"
        render={record => record.last_error || '—'}
      />
    </Datagrid>
  </List>
);

// (Optional) Default export for convenience
export default PipelineDashboard;
