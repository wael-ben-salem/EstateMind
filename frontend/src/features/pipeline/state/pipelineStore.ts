import { create } from 'zustand';

type PipelineStore = {
  lastRunId: string | null;
  lastRunState: string | null;
  lastRunScore: number;
  setLastRun: (run: { runId: string; state: string; score: number }) => void;
};

export const usePipelineStore = create<PipelineStore>((set) => ({
  lastRunId: null,
  lastRunState: null,
  lastRunScore: 70,
  setLastRun: (run) => set({ lastRunId: run.runId, lastRunState: run.state, lastRunScore: run.score })
}));

