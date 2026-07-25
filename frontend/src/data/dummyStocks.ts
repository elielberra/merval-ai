import type { Stock } from "../types";

export const dummyStocks: Stock[] = [
  {
    ticker: "GGAL",
    description: "Grupo Financiero Galicia",
    currency: "ARS",
    type: "ACCIONES",
    market: "BYMA",
    settlement: "A-24HS",
    quantity: 50,
    boughtPrice: 6200,
    currentPrice: 6450,
  },
  {
    ticker: "YPFD",
    description: "YPF S.A.",
    currency: "ARS",
    type: "ACCIONES",
    market: "BYMA",
    settlement: "A-24HS",
    quantity: 10,
    boughtPrice: 38500,
    currentPrice: 37100,
  },
];
