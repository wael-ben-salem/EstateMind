import { Box, Card, CardContent, Grid, Stack, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';
import { WorkflowCanvas } from '@/features/pipeline/workflow/WorkflowCanvas';
import { PipelineRunPanel } from '@/features/pipeline/components/PipelineRunPanel';

export function WorkflowOrchestrator() {
  return (
    <Box>
      <PageHeader
        title="Workflow Orchestrator"
        subtitle="Builder visuel (React Flow) + exécution (via Airflow trigger)."
      />

      <Grid container spacing={2}>
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Stack spacing={0.75} sx={{ mb: 1 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 900 }}>
                  Workflow Canvas
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Drag-and-drop, connexions, mini-map, export/import (MVP).
                </Typography>
              </Stack>
              <WorkflowCanvas />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} lg={4}>
          <PipelineRunPanel />
        </Grid>
      </Grid>
    </Box>
  );
}

