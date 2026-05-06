import { Box, Typography } from '@mui/material';
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const mock = [
  { step: 'Scrape', value: 12000 },
  { step: 'Dedup', value: -1800 },
  { step: 'Regex', value: -600 },
  { step: 'LLM', value: -220 },
  { step: 'Geo', value: -140 },
  { step: 'Valid', value: -90 },
  { step: 'Loaded', value: 9150 }
];

export function WaterfallDataFlow() {
  return (
    <Box sx={{ height: 260 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={mock} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="step" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#3b82f6">
            <LabelList dataKey="value" position="top" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <Typography variant="caption" color="text.secondary">
        MVP: valeurs mock. On branchera ces barres sur les métriques réelles (Airflow logs + validator + ETL).
      </Typography>
    </Box>
  );
}

