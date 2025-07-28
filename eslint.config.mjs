import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
	{ files: ['**/*.{js,mjs,cjs,ts,mts,cts}'], languageOptions: { globals: globals.node } },
	...tseslint.configs.recommended,
	{
		rules: {
			// Formatting rules
			'indent': ['error', 'tab'],
			'quotes': ['error', 'single'],
			'semi': ['error', 'always'],
			'comma-dangle': ['error', 'always-multiline'],
			'no-trailing-spaces': 'error',
			'object-curly-spacing': ['error', 'always'],
			'array-bracket-spacing': ['error', 'never'],
			'brace-style': ['error', '1tbs'],
			'keyword-spacing': 'error',
			'space-before-blocks': 'error',
			'space-infix-ops': 'error',
			'no-multiple-empty-lines': ['error', { 'max': 1 }],
			'eol-last': ['error', 'always'],
			'@typescript-eslint/no-unused-vars': ['error', { 'argsIgnorePattern': '^_' }],
			'prefer-const': 'error',
		},
	},
);
