import { Navigate, Route, Routes } from 'react-router-dom';

import { MainLayout } from '@/app/layout/MainLayout';
import { ExecutiveDashboard } from '@/features/dashboard/pages/ExecutiveDashboard';
import { OperationalDashboard } from '@/features/dashboard/pages/OperationalDashboard';
import { CustomDashboardBuilder } from '@/features/dashboard/pages/CustomDashboardBuilder';
import { WorkflowOrchestrator } from '@/features/pipeline/pages/WorkflowOrchestrator';
import { DataCatalog } from '@/features/data-market/pages/DataCatalog';
import { DataLineage } from '@/features/data-market/pages/DataLineage';
import { QualityScoreboard } from '@/features/data-market/pages/QualityScoreboard';
import { MarketIntelligence } from '@/features/analytics/pages/MarketIntelligence';
import { PricePrediction } from '@/features/analytics/pages/PricePrediction';
import { InvestmentAnalyzer } from '@/features/analytics/pages/InvestmentAnalyzer';
import { SystemHealth } from '@/features/admin/pages/SystemHealth';
import { AuditTrail } from '@/features/admin/pages/AuditTrail';
import { ConfigurationHub } from '@/features/admin/pages/ConfigurationHub';

export function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/dashboard/executive" element={<ExecutiveDashboard />} />
        <Route path="/dashboard/operational" element={<OperationalDashboard />} />
        <Route path="/dashboard/builder" element={<CustomDashboardBuilder />} />

        <Route path="/pipeline" element={<WorkflowOrchestrator />} />

        <Route path="/data/catalog" element={<DataCatalog />} />
        <Route path="/data/lineage" element={<DataLineage />} />
        <Route path="/data/quality" element={<QualityScoreboard />} />

        <Route path="/analytics/market" element={<MarketIntelligence />} />
        <Route path="/analytics/predict" element={<PricePrediction />} />
        <Route path="/analytics/invest" element={<InvestmentAnalyzer />} />

        <Route path="/admin/health" element={<SystemHealth />} />
        <Route path="/admin/audit" element={<AuditTrail />} />
        <Route path="/admin/config" element={<ConfigurationHub />} />
      </Route>

      <Route path="/" element={<Navigate to="/dashboard/executive" replace />} />
      <Route path="*" element={<Navigate to="/dashboard/executive" replace />} />
    </Routes>
  );
}

