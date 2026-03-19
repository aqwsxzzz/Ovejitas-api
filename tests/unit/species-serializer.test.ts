import { describe, it, expect } from 'vitest';
import { SpeciesSerializer } from '../../src/resources/species/species.serializer';
import { encodeId } from '../../src/utils/id-hash-util';
import { SpeciesModel } from '../../src/resources/species/species.model';
import { SpeciesTranslationModel } from '../../src/resources/species-translation/species-translation.model';

function makeSpecies(overrides?: Partial<SpeciesModel>): SpeciesModel {
	return {
		id: 1,
		createdAt: '2025-01-01T00:00:00.000Z',
		updatedAt: '2025-01-01T00:00:00.000Z',
		...overrides,
	} as SpeciesModel;
}

function makeTranslation(overrides?: Partial<SpeciesTranslationModel>): SpeciesTranslationModel {
	return {
		id: 10,
		speciesId: 1,
		language: 'en',
		name: 'Sheep',
		createdAt: '2025-01-01T00:00:00.000Z',
		updatedAt: '2025-01-01T00:00:00.000Z',
		...overrides,
	} as SpeciesTranslationModel;
}

describe('SpeciesSerializer', () => {
	describe('serialize', () => {
		it('encodes the id as a hash', () => {
			const species = makeSpecies({ id: 42 });
			const result = SpeciesSerializer.serialize(species);
			expect(result.id).toBe(encodeId(42));
		});

		it('includes createdAt and updatedAt', () => {
			const species = makeSpecies();
			const result = SpeciesSerializer.serialize(species);
			expect(result.createdAt).toBe('2025-01-01T00:00:00.000Z');
			expect(result.updatedAt).toBe('2025-01-01T00:00:00.000Z');
		});

		it('omits translations when not present on model', () => {
			const species = makeSpecies();
			const result = SpeciesSerializer.serialize(species);
			expect(result.translations).toBeUndefined();
		});

		it('includes serialized translations when present', () => {
			const species = makeSpecies({ id: 1 }) as SpeciesModel & { translations: SpeciesTranslationModel[] };
			species.translations = [makeTranslation({ id: 10, speciesId: 1 })];
			const result = SpeciesSerializer.serialize(species);
			expect(result.translations).toHaveLength(1);
			expect(result.translations![0].id).toBe(encodeId(10));
			expect(result.translations![0].name).toBe('Sheep');
		});
	});

	describe('serializeMany', () => {
		it('serializes an array of species', () => {
			const species = [makeSpecies({ id: 1 }), makeSpecies({ id: 2 })];
			const result = SpeciesSerializer.serializeMany(species);
			expect(result).toHaveLength(2);
			expect(result[0].id).toBe(encodeId(1));
			expect(result[1].id).toBe(encodeId(2));
		});
	});
});
