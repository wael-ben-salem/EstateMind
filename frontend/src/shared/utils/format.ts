export function formatNumber(value: number) {
  return new Intl.NumberFormat('fr-TN').format(value);
}

export function formatCurrencyTND(value: number) {
  return new Intl.NumberFormat('fr-TN', { style: 'currency', currency: 'TND', maximumFractionDigits: 0 }).format(
    value,
  );
}

