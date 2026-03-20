import { FastifyInstance } from 'fastify';
import { encodeId } from '../../src/utils/id-hash-util';

export async function createSpecies(
	app: FastifyInstance,
	overrides?: { name?: string; language?: string },
): Promise<{ speciesId: number; translationId: number }> {
	const species = await app.db.models.Species.create({});
	const translation = await app.db.models.SpeciesTranslation.create({
		speciesId: species.dataValues.id,
		name: overrides?.name ?? 'Sheep',
		language: overrides?.language ?? 'en',
	});

	return {
		speciesId: species.dataValues.id,
		translationId: translation.dataValues.id,
	};
}

export async function createBreed(
	app: FastifyInstance,
	speciesId: number,
	overrides?: { name?: string; language?: string },
): Promise<{ breedId: number; translationId: number }> {
	const breed = await app.db.models.Breed.create({ speciesId });
	const translation = await app.db.models.BreedTranslation.create({
		breedId: breed.dataValues.id,
		name: overrides?.name ?? 'Merino',
		language: overrides?.language ?? 'en',
	});

	return {
		breedId: breed.dataValues.id,
		translationId: translation.dataValues.id,
	};
}

export async function createFarm(
	app: FastifyInstance,
	userId: number,
	overrides?: { name?: string },
): Promise<{ farmId: number }> {
	const farm = await app.db.models.Farm.create({
		name: overrides?.name ?? 'Test Farm',
	});

	await app.db.models.FarmMember.create({
		farmId: farm.dataValues.id,
		userId,
		role: 'owner',
	});

	return { farmId: farm.dataValues.id };
}

export async function createAnimal(
	app: FastifyInstance,
	farmId: number,
	speciesId: number,
	breedId: number,
	overrides?: { tagNumber?: string; name?: string; sex?: string; groupName?: string },
): Promise<{ animalId: number; encodedAnimalId: string }> {
	const animal = await app.db.models.Animal.create({
		farmId,
		speciesId,
		breedId,
		tagNumber: overrides?.tagNumber ?? `TAG-${Date.now()}`,
		name: overrides?.name ?? 'Test Animal',
		sex: overrides?.sex ?? 'unknown',
		...(overrides?.groupName ? { groupName: overrides.groupName } : {}),
	});

	return {
		animalId: animal.dataValues.id,
		encodedAnimalId: encodeId(animal.dataValues.id),
	};
}

export async function createMeasurement(
	app: FastifyInstance,
	animalId: number,
	measuredBy: number,
	overrides?: { measurementType?: string; value?: number; unit?: string; measuredAt?: string; notes?: string },
): Promise<{ measurementId: number; encodedMeasurementId: string }> {
	const measurement = await app.db.models.AnimalMeasurement.create({
		animalId,
		measurementType: overrides?.measurementType ?? 'weight',
		value: overrides?.value ?? 50.0,
		unit: overrides?.unit ?? 'kg',
		measuredAt: overrides?.measuredAt ?? new Date().toISOString(),
		measuredBy,
		notes: overrides?.notes,
	});

	return {
		measurementId: measurement.dataValues.id,
		encodedMeasurementId: encodeId(measurement.dataValues.id),
	};
}

export async function createFlock(
	app: FastifyInstance,
	farmId: number,
	speciesId: number,
	breedId: number,
	overrides?: {
		name?: string;
		flockType?: string;
		initialCount?: number;
		status?: string;
		startDate?: string;
		acquisitionType?: string;
		endDate?: string;
		houseName?: string;
		ageAtAcquisitionWeeks?: number;
		notes?: string;
	},
): Promise<{ flockId: number; encodedFlockId: string }> {
	const initialCount = overrides?.initialCount ?? 100;
	const flock = await app.db.models.Flock.create({
		farmId,
		speciesId,
		breedId,
		name: overrides?.name ?? `Flock-${Date.now()}`,
		flockType: overrides?.flockType ?? 'general',
		initialCount,
		currentCount: initialCount,
		status: overrides?.status ?? 'active',
		startDate: overrides?.startDate ?? '2025-01-01',
		acquisitionType: overrides?.acquisitionType ?? 'purchased',
		...(overrides?.endDate ? { endDate: overrides.endDate } : {}),
		...(overrides?.houseName ? { houseName: overrides.houseName } : {}),
		...(overrides?.ageAtAcquisitionWeeks !== undefined ? { ageAtAcquisitionWeeks: overrides.ageAtAcquisitionWeeks } : {}),
		...(overrides?.notes ? { notes: overrides.notes } : {}),
	});

	return {
		flockId: flock.dataValues.id,
		encodedFlockId: encodeId(flock.dataValues.id),
	};
}

export async function createExpense(
	app: FastifyInstance,
	farmId: number,
	createdBy: number,
	overrides?: { amount?: number; category?: string; date?: string },
): Promise<{ expenseId: number; encodedExpenseId: string }> {
	const expense = await app.db.models.Expense.create({
		farmId,
		createdBy,
		date: overrides?.date ?? '2025-01-15',
		amount: overrides?.amount ?? 100.00,
		category: overrides?.category ?? 'feed',
	});

	return {
		expenseId: expense.dataValues.id,
		encodedExpenseId: encodeId(expense.dataValues.id),
	};
}
