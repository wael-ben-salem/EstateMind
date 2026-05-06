import { useQuery } from '@tanstack/react-query';
import { estateMindApi } from '@/shared/api/estateMindApi';

export function useExecutiveSummary() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: estateMindApi.stats,
    refetchInterval: 30_000
  });
}

