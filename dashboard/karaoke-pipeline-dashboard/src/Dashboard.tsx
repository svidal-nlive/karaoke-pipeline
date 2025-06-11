import * as React from "react";
import { List, Datagrid, TextField, FunctionField, Button } from 'react-admin';
import { useNotify, useRefresh, useDataProvider, RaRecord } from 'react-admin';

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
          label="Retry"
          onClick={async () => {
            try {
              await dataProvider.create('retry', { data: { filename: record.filename } });
              notify('Retry triggered for ' + record.filename, { type: 'info' });
              refresh();
            }
              catch (err: any) {
                notify('Retry failed: ' + (err && err.message), { type: 'error' });
              }
          }}
          disabled={record.status !== "error"}
        />
      }
    />
  );
};
