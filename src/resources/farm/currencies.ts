export const SUPPORTED_CURRENCIES = [
	{ code: 'USD', name: 'US Dollar', symbol: '$' },
	{ code: 'EUR', name: 'Euro', symbol: '€' },
	{ code: 'GBP', name: 'British Pound', symbol: '£' },
	{ code: 'MXN', name: 'Mexican Peso', symbol: '$' },
	{ code: 'ARS', name: 'Argentine Peso', symbol: '$' },
	{ code: 'BRL', name: 'Brazilian Real', symbol: 'R$' },
	{ code: 'CLP', name: 'Chilean Peso', symbol: '$' },
	{ code: 'COP', name: 'Colombian Peso', symbol: '$' },
	{ code: 'PEN', name: 'Peruvian Sol', symbol: 'S/' },
	{ code: 'UYU', name: 'Uruguayan Peso', symbol: '$U' },
	{ code: 'CAD', name: 'Canadian Dollar', symbol: 'C$' },
	{ code: 'AUD', name: 'Australian Dollar', symbol: 'A$' },
	{ code: 'JPY', name: 'Japanese Yen', symbol: '¥' },
	{ code: 'CHF', name: 'Swiss Franc', symbol: 'CHF' },
	{ code: 'CNY', name: 'Chinese Yuan', symbol: '¥' },
] as const;

export type CurrencyCode = (typeof SUPPORTED_CURRENCIES)[number]['code'];

export const CURRENCY_CODES = SUPPORTED_CURRENCIES.map(c => c.code) as readonly CurrencyCode[];
