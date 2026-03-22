import { describe, it, expect } from 'vitest';
import { FlockSerializer } from '../../src/resources/flock/flock.serializer';
import { encodeId } from '../../src/utils/id-hash-util';
import { FlockWithPossibleIncludes } from '../../src/resources/flock/flock.schema';

function makeFlock(overrides?: Partial<FlockWithPossibleIncludes>): FlockWithPossibleIncludes {
	return {
		id: 1,
		farmId: 10,
		speciesId: 20,
		breedId: 30,
		name: 'Test Flock',
		flockType: 'general',
		initialCount: 100,
		currentCount: 100,
		status: 'active',
		startDate: '2025-01-01',
		endDate: null,
		houseName: null,
		acquisitionType: 'purchased',
		ageAtAcquisitionWeeks: null,
		notes: null,
		createdAt: '2025-01-01T00:00:00.000Z',
		updatedAt: '2025-01-01T00:00:00.000Z',
		...overrides,
	} as FlockWithPossibleIncludes;
}

describe('FlockSerializer', () => {
	describe('serialize', () => {
		it('encodes all id fields as hashes', () => {
			const flock = makeFlock({ id: 1, farmId: 10, speciesId: 20, breedId: 30 });
			const result = FlockSerializer.serialize(flock);
			expect(result.id).toBe(encodeId(1));
			expect(result.farmId).toBe(encodeId(10));
			expect(result.speciesId).toBe(encodeId(20));
			expect(result.breedId).toBe(encodeId(30));
		});

		it('includes scalar fields directly', () => {
			const flock = makeFlock({
				name: 'Layers A',
				flockType: 'layers',
				initialCount: 50,
				currentCount: 45,
				status: 'active',
				startDate: '2025-03-01',
				acquisitionType: 'hatched',
			});
			const result = FlockSerializer.serialize(flock);
			expect(result.name).toBe('Layers A');
			expect(result.flockType).toBe('layers');
			expect(result.initialCount).toBe(50);
			expect(result.currentCount).toBe(45);
			expect(result.status).toBe('active');
			expect(result.startDate).toBe('2025-03-01');
			expect(result.acquisitionType).toBe('hatched');
		});

		it('handles nullable fields when null', () => {
			const flock = makeFlock({
				endDate: null,
				houseName: null,
				ageAtAcquisitionWeeks: null,
				notes: null,
			});
			const result = FlockSerializer.serialize(flock);
			expect(result.endDate).toBeNull();
			expect(result.houseName).toBeNull();
			expect(result.ageAtAcquisitionWeeks).toBeNull();
			expect(result.notes).toBeNull();
		});

		it('includes species relation when present', () => {
			const flock = makeFlock({
				species: {
					id: 20,
					createdAt: '2025-01-01T00:00:00.000Z',
					updatedAt: '2025-01-01T00:00:00.000Z',
					translations: [
						{
							id: 1,
							speciesId: 20,
							language: 'en',
							name: 'Chicken',
							createdAt: '2025-01-01T00:00:00.000Z',
							updatedAt: '2025-01-01T00:00:00.000Z',
						},
					],
				} as FlockWithPossibleIncludes['species'],
			});
			const result = FlockSerializer.serialize(flock);
			expect(result.species).toBeDefined();
			expect(result.species!.id).toBe(encodeId(20));
			expect(result.species!.translations).toHaveLength(1);
			expect(result.species!.translations![0].name).toBe('Chicken');
		});

		it('omits species when not present', () => {
			const flock = makeFlock();
			const result = FlockSerializer.serialize(flock);
			expect(result.species).toBeUndefined();
		});

		it('includes breed relation when present', () => {
			const flock = makeFlock({
				breed: {
					id: 30,
					speciesId: 20,
					createdAt: '2025-01-01T00:00:00.000Z',
					updatedAt: '2025-01-01T00:00:00.000Z',
					translations: [
						{
							id: 2,
							breedId: 30,
							language: 'en',
							name: 'Leghorn',
							createdAt: '2025-01-01T00:00:00.000Z',
							updatedAt: '2025-01-01T00:00:00.000Z',
						},
					],
				} as FlockWithPossibleIncludes['breed'],
			});
			const result = FlockSerializer.serialize(flock);
			expect(result.breed).toBeDefined();
			expect(result.breed!.id).toBe(encodeId(30));
			expect(result.breed!.speciesId).toBe(encodeId(20));
			expect(result.breed!.translations).toHaveLength(1);
			expect(result.breed!.translations![0].name).toBe('Leghorn');
		});

		it('omits breed when not present', () => {
			const flock = makeFlock();
			const result = FlockSerializer.serialize(flock);
			expect(result.breed).toBeUndefined();
		});
	});

	describe('serializeMany', () => {
		it('serializes an array of flocks', () => {
			const flocks = [makeFlock({ id: 1 }), makeFlock({ id: 2 })];
			const result = FlockSerializer.serializeMany(flocks);
			expect(result).toHaveLength(2);
			expect(result[0].id).toBe(encodeId(1));
			expect(result[1].id).toBe(encodeId(2));
		});
	});
});
