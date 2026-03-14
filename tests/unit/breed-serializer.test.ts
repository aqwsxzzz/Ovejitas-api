import { describe, it, expect } from 'vitest';
import { BreedSerializer } from '../../src/resources/breed/breed.serializer';
import { encodeId } from '../../src/utils/id-hash-util';
import { BreedModel } from '../../src/resources/breed/breed.model';
import { BreedTranslationModel } from '../../src/resources/breed-translation/breed-translation.model';

function makeBreed(overrides?: Partial<BreedModel>): BreedModel {
	return {
		id: 1,
		speciesId: 10,
		createdAt: '2025-01-01T00:00:00.000Z',
		updatedAt: '2025-01-01T00:00:00.000Z',
		...overrides,
	} as BreedModel;
}

function makeTranslation(overrides?: Partial<BreedTranslationModel>): BreedTranslationModel {
	return {
		id: 50,
		breedId: 1,
		language: 'en',
		name: 'Merino',
		createdAt: '2025-01-01T00:00:00.000Z',
		updatedAt: '2025-01-01T00:00:00.000Z',
		...overrides,
	} as BreedTranslationModel;
}

describe('BreedSerializer', () => {
	describe('serialize', () => {
		it('encodes id and speciesId', () => {
			const breed = makeBreed({ id: 5, speciesId: 10 });
			const result = BreedSerializer.serialize(breed);
			expect(result.id).toBe(encodeId(5));
			expect(result.speciesId).toBe(encodeId(10));
		});

		it('includes timestamps', () => {
			const breed = makeBreed();
			const result = BreedSerializer.serialize(breed);
			expect(result.createdAt).toBe('2025-01-01T00:00:00.000Z');
			expect(result.updatedAt).toBe('2025-01-01T00:00:00.000Z');
		});

		it('omits translations when not present', () => {
			const breed = makeBreed();
			const result = BreedSerializer.serialize(breed);
			expect(result.translations).toBeUndefined();
		});

		it('includes translations from model when present', () => {
			const breed = makeBreed() as BreedModel & { translations: BreedTranslationModel[] };
			breed.translations = [makeTranslation()];
			const result = BreedSerializer.serialize(breed);
			expect(result.translations).toHaveLength(1);
			expect(result.translations![0].name).toBe('Merino');
			expect(result.translations![0].id).toBe(encodeId(50));
		});

		it('prefers explicit translations param over model translations', () => {
			const breed = makeBreed() as BreedModel & { translations: BreedTranslationModel[] };
			breed.translations = [makeTranslation({ name: 'FromModel' })];
			const explicitTranslations = [makeTranslation({ name: 'Explicit' })];
			const result = BreedSerializer.serialize(breed, explicitTranslations);
			expect(result.translations![0].name).toBe('Explicit');
		});
	});

	describe('serializeMany', () => {
		it('serializes an array of breeds', () => {
			const breeds = [makeBreed({ id: 1 }), makeBreed({ id: 2 })];
			const result = BreedSerializer.serializeMany(breeds);
			expect(result).toHaveLength(2);
			expect(result[0].id).toBe(encodeId(1));
			expect(result[1].id).toBe(encodeId(2));
		});
	});
});
