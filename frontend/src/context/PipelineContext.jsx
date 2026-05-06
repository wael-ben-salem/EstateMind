import React, { createContext, useState, useCallback } from 'react';
import { airflowService } from '../services/airflowService';

export const PipelineContext = createContext();

export const PipelineProvider = ({ children }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [dagRunId, setDagRunId] = useState(null);

  const updatePipelineStatus = useCallback(async (runId) => {
    try {
      const status = await airflowService.getPipelineStatus(runId);
      console.log('[PIPELINE] Status update:', status);
      
      if (status.steps) {
        setSteps(status.steps);
      }

      if (status.state === 'success' || status.state === 'failed') {
        setIsRunning(false);
        console.log(`[PIPELINE] Pipeline ${status.state}`);
        return true; // Pipeline finished
      }
      return false; // Pipeline still running
    } catch (error) {
      console.error('[PIPELINE] Error fetching status:', error);
      return false;
    }
  }, []);

  const triggerPipeline = useCallback(async () => {
    console.log('[PIPELINE] Triggering pipeline...');
    setIsRunning(true);
    setCurrentStep(0);
    setSteps([]);
    
    try {
      const response = await airflowService.triggerPipeline();
      console.log('[PIPELINE] Response:', response);
      
      const runId = response.dag_run_id;
      setDagRunId(runId);
      console.log('[PIPELINE] DAG Run ID:', runId);

      // Poll for status updates
      const pollInterval = setInterval(async () => {
        const isFinished = await updatePipelineStatus(runId);
        if (isFinished) {
          clearInterval(pollInterval);
        }
      }, 3000); // Poll every 3 seconds

      return runId;
    } catch (error) {
      console.error('[PIPELINE] Error triggering pipeline:', error);
      setIsRunning(false);
      alert('Failed to start pipeline. Check browser console for details.');
      throw error;
    }
  }, [updatePipelineStatus]);

  return (
    <PipelineContext.Provider value={{
      isRunning,
      steps,
      currentStep,
      dagRunId,
      triggerPipeline,
      setSteps
    }}>
      {children}
    </PipelineContext.Provider>
  );
};
