import { describe, it, expect } from 'vitest';
import { AnimalSerializer } from '../../src/resources/animal/animal.serializer';
import { encodeId } from '../../src/utils/id-hash-util';
import { AnimalWithPossibleIncludes } from '../../src/resources/animal/animal.schema';

function makeAnimal(overrides?: Partial<AnimalWithPossibleIncludes>): AnimalWithPossibleIncludes {
	return {
		id: 1,
		farmId: 10,
		speciesId: 20,
		breedId: 30,
		name: 'Dolly',
		tagNumber: 'TAG-001',
		sex: 'female',
		birthDate: '2024-01-01',
		status: 'alive',
		reproductiveStatus: 'open',
		fatherId: null,
		motherId: null,
		acquisitionType: 'born',
		acquisitionDate: '2024-01-01',
		createdAt: '2025-01-01T00:00:00.000Z',
		updatedAt: '2025-01-01T00:00:00.000Z',
		weightId: null,
		groupName: 'Group A',
		...overrides,
	} as AnimalWithPossibleIncludes;
}

describe('AnimalSerializer', () => {
	describe('serialize', () => {
		it('encodes all id fields as hashes', () => {
			const animal = makeAnimal({ id: 1, farmId: 10, speciesId: 20, breedId: 30 });
			const result = AnimalSerializer.serialize(animal);
			expect(result.id).toBe(encodeId(1));
			expect(result.farmId).toBe(encodeId(10));
			expect(result.speciesId).toBe(encodeId(20));
			expect(result.breedId).toBe(encodeId(30));
		});

		it('encodes parentIds when present', () => {
			const animal = makeAnimal({ fatherId: 5, motherId: 6 });
			const result = AnimalSerializer.serialize(animal);
			expect(result.fatherId).toBe(encodeId(5));
			expect(result.motherId).toBe(encodeId(6));
		});

		it('returns empty string for parentIds when null', () => {
			const animal = makeAnimal({ fatherId: null, motherId: null });
			const result = AnimalSerializer.serialize(animal);
			expect(result.fatherId).toBe('');
			expect(result.motherId).toBe('');
		});

		it('includes scalar fields directly', () => {
			const animal = makeAnimal({ name: 'Dolly', tagNumber: 'TAG-001', sex: 'female', status: 'alive' });
			const result = AnimalSerializer.serialize(animal);
			expect(result.name).toBe('Dolly');
			expect(result.tagNumber).toBe('TAG-001');
			expect(result.sex).toBe('female');
			expect(result.status).toBe('alive');
		});

		it('includes species relation when present', () => {
			const animal = makeAnimal({
				species: {
					id: 20,
					createdAt: '2025-01-01T00:00:00.000Z',
					updatedAt: '2025-01-01T00:00:00.000Z',
				} as AnimalWithPossibleIncludes['species'],
			});
			const result = AnimalSerializer.serialize(animal);
			expect(result.species).toBeDefined();
			expect(result.species!.id).toBe(encodeId(20));
		});

		it('omits species when not present', () => {
			const animal = makeAnimal();
			const result = AnimalSerializer.serialize(animal);
			expect(result.species).toBeUndefined();
		});

		it('includes breed relation when present', () => {
			const animal = makeAnimal({
				breed: {
					id: 30,
					speciesId: 20,
					createdAt: '2025-01-01T00:00:00.000Z',
					updatedAt: '2025-01-01T00:00:00.000Z',
				} as AnimalWithPossibleIncludes['breed'],
			});
			const result = AnimalSerializer.serialize(animal);
			expect(result.breed).toBeDefined();
			expect(result.breed!.id).toBe(encodeId(30));
		});

		it('includes father relation when present', () => {
			const animal = makeAnimal({
				father: {
					id: 5,
					name: 'Dad',
					tagNumber: 'TAG-F01',
					createdAt: '2025-01-01T00:00:00.000Z',
					updatedAt: '2025-01-01T00:00:00.000Z',
				} as AnimalWithPossibleIncludes['father'],
			});
			const result = AnimalSerializer.serialize(animal);
			expect(result.father).toBeDefined();
			expect(result.father!.id).toBe(encodeId(5));
			expect(result.father!.name).toBe('Dad');
		});
	});

	describe('serializeMany', () => {
		it('serializes an array of animals', () => {
			const animals = [makeAnimal({ id: 1 }), makeAnimal({ id: 2 })];
			const result = AnimalSerializer.serializeMany(animals);
			expect(result).toHaveLength(2);
			expect(result[0].id).toBe(encodeId(1));
			expect(result[1].id).toBe(encodeId(2));
		});
	});
});
