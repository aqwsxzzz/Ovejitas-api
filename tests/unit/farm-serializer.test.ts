import { describe, it, expect } from 'vitest';
import { FarmSerializer } from '../../src/resources/farm/farm.serializer';
import { encodeId } from '../../src/utils/id-hash-util';
import { FarmModel } from '../../src/resources/farm/farm.model';

function makeFarm(overrides?: Record<string, unknown>): FarmModel {
	return {
		dataValues: {
			id: 1,
			name: 'Test Farm',
			createdAt: '2025-01-01T00:00:00.000Z',
			updatedAt: '2025-01-01T00:00:00.000Z',
			...overrides,
		},
	} as unknown as FarmModel;
}

describe('FarmSerializer', () => {
	describe('serialize', () => {
		it('encodes the farm id', () => {
			const farm = makeFarm({ id: 42 });
			const result = FarmSerializer.serialize(farm);
			expect(result.id).toBe(encodeId(42));
		});

		it('includes name and timestamps', () => {
			const farm = makeFarm({ name: 'My Ranch' });
			const result = FarmSerializer.serialize(farm);
			expect(result.name).toBe('My Ranch');
			expect(result.createdAt).toBe('2025-01-01T00:00:00.000Z');
			expect(result.updatedAt).toBe('2025-01-01T00:00:00.000Z');
		});
	});

	describe('serializeMany', () => {
		it('serializes an array of farms', () => {
			const farms = [makeFarm({ id: 1 }), makeFarm({ id: 2 })];
			const result = FarmSerializer.serializeMany(farms);
			expect(result).toHaveLength(2);
			expect(result[0].id).toBe(encodeId(1));
			expect(result[1].id).toBe(encodeId(2));
		});
	});
});
