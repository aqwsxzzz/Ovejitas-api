import { describe, it, expect } from 'vitest';
import { encodeId, decodeId } from '../../src/utils/id-hash-util';

describe('encodeId / decodeId', () => {
	it('round-trips a positive integer', () => {
		const encoded = encodeId(42);
		const decoded = decodeId(encoded);
		expect(decoded).toBe(42);
	});

	it('round-trips id of 1', () => {
		const encoded = encodeId(1);
		const decoded = decodeId(encoded);
		expect(decoded).toBe(1);
	});

	it('produces different hashes for different ids', () => {
		const hash1 = encodeId(1);
		const hash2 = encodeId(2);
		expect(hash1).not.toBe(hash2);
	});

	it('throws for an invalid hash string with non-alphabet characters', () => {
		expect(() => decodeId('invalid-hash-string')).toThrow();
	});

	it('returns undefined for an empty string', () => {
		const result = decodeId('');
		expect(result).toBeUndefined();
	});
});
