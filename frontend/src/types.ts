export interface Stock {
  ticker: string;
  description: string;
  currency: string;
  type: string;
  market: string;
  settlement: string;
  quantity: number;
  boughtPrice: number;
  currentPrice: number;
}
