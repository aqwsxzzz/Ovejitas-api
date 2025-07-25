import { FastifyReply, FastifyRequest } from 'fastify';
import { Animal } from '../../models/animal-model';
import { AnimalMeasurement } from '../../models/animal-measurement-model';
import { serializeAnimal } from '../../serializers/animal-serializer';
import { decodeId, encodeId } from '../../utils/id-hash-util';
import { findAnimalById, findAnimalsByFarmId, isTagNumberUniqueForFarm, validateParentSex } from '../../utils/animal-util';
import { AnimalCreateRoute, AnimalUpdateRoute, AnimalGetRoute, AnimalDeleteRoute, AnimalListRoute, AnimalListByFarmRoute } from '../../types/animal-types';
import { findBreedById } from '../../utils/breed-util';

export const createAnimal = async (request: FastifyRequest<AnimalCreateRoute>, reply: FastifyReply) => {
	try {
		const { speciesId, breedId, name, tagNumber, sex, birthDate, weight, status, reproductiveStatus, fatherId, motherId, acquisitionType, acquisitionDate } = request.body;
		const { farmId } = request.params;
		const farmIdDecoded = decodeId(farmId)!;
		const speciesIdDecoded = decodeId(speciesId)!;
		if (!breedId) {
			return reply.code(400).send({ message: 'Breed ID is required.' });
		}
		const breedIdDecoded = decodeId(breedId)!;
		const fatherIdDecoded = fatherId ? decodeId(fatherId) : null;
		const motherIdDecoded = motherId ? decodeId(motherId) : null;

		// Validate parent sex
		let father: Animal | null = null;
		let mother: Animal | null = null;
		if (fatherIdDecoded) father = await Animal.findByPk(fatherIdDecoded);
		if (motherIdDecoded) mother = await Animal.findByPk(motherIdDecoded);
		const parentSexError = validateParentSex(father, mother);
		if (parentSexError) {
			return reply.code(400).send({ message: parentSexError });
		}

		// Validate breed-species match
		const breed = await findBreedById(breedId);
		if (!breed) {
			return reply.code(400).send({ message: 'Breed not found.' });
		}
		if (breed.speciesId !== speciesIdDecoded) {
			return reply.code(400).send({ message: 'Selected breed does not belong to the specified species. Please select a valid breed for this species.' });
		}

		// Check tag number requirement and uniqueness
		if (!tagNumber) {
			return reply.code(400).send({ message: 'Tag number is required.' });
		}
		const isUnique = await isTagNumberUniqueForFarm(tagNumber, farmIdDecoded, speciesIdDecoded);
		if (!isUnique) {
			return reply.code(409).send({ message: 'Tag number must be unique per farm and species.' });
		}
		const animal = await Animal.create({
			farmId: farmIdDecoded,
			speciesId: speciesIdDecoded,
			breedId: breedIdDecoded,
			name,
			tagNumber: tagNumber,
			sex,
			birthDate: new Date(birthDate),
			weight: weight ?? null,
			status,
			reproductiveStatus,
			fatherId: fatherIdDecoded,
			motherId: motherIdDecoded,
			acquisitionType,
			acquisitionDate: new Date(acquisitionDate),
		});

		// Create initial weight measurement if weight is provided
		if (weight) {
			await AnimalMeasurement.create({
				animalId: animal.id,
				measurementType: 'weight',
				value: weight,
				unit: 'kg',
				measuredAt: new Date(),
				measuredBy: request.user?.id || null,
				method: 'initial',
				notes: 'Initial weight measurement',
			});
		}

		// Reload the animal with associations
		const animalWithAssociations = await findAnimalById(encodeId(animal.id));
		return reply.code(201).send(serializeAnimal(animalWithAssociations!, request?.language || 'en'));
	} catch (error) {
		console.error(error);
		return reply.code(500).send({ message: 'Internal server error', error: error });
	}
};

export const listAnimalsByFarm = async (request: FastifyRequest<AnimalListByFarmRoute>, reply: FastifyReply) => {
	const { farmId } = request.params;

	if (!farmId) {
		return reply.code(400).send({ message: 'farmId is required' });
	}
	const animals = await findAnimalsByFarmId(farmId);

	// Map each animal through serializeAnimal with await using Promise.all
	reply.send(animals.map((animal) => serializeAnimal(animal, request?.language || 'en')));
};

export const getAnimalById = async (request: FastifyRequest<AnimalGetRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const animal = await findAnimalById(id);
	if (!animal) {
		return reply.code(404).send({ message: 'Animal not found' });
	}
	reply.send(serializeAnimal(animal, request?.language || 'en'));
};

export const updateAnimal = async (request: FastifyRequest<AnimalUpdateRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const animal = await findAnimalById(id);
	if (!animal) {
		return reply.code(404).send({ message: 'Animal not found' });
	}
	const { speciesId, breedId, name, tagNumber, sex, birthDate, weight, status, reproductiveStatus, fatherId, motherId, acquisitionType, acquisitionDate } = request.body;
	const { farmId } = request.params;
	if (tagNumber) {
		const farmIdToUse = farmId ? decodeId(farmId)! : animal.farmId;
		const speciesIdToUse = speciesId ? decodeId(speciesId)! : animal.speciesId;
		const isUnique = await isTagNumberUniqueForFarm(tagNumber, farmIdToUse, speciesIdToUse, animal.id);
		if (!isUnique) {
			return reply.code(409).send({ message: 'Tag number must be unique per farm and species.' });
		}
	}
	if (farmId) animal.set('farmId', decodeId(farmId)!);
	if (speciesId) animal.set('speciesId', decodeId(speciesId)!);
	if (breedId !== undefined) {
		if (!breedId) {
			return reply.code(400).send({ message: 'Breed ID is required.' });
		}
		animal.set('breedId', decodeId(breedId)!);
	}
	if (name) animal.set('name', name);
	if (tagNumber !== undefined) {
		if (!tagNumber) {
			return reply.code(400).send({ message: 'Tag number is required.' });
		}
		animal.set('tagNumber', tagNumber);
	}
	if (sex) animal.set('sex', sex);
	if (birthDate) animal.set('birthDate', new Date(birthDate));
	if (weight !== undefined) animal.set('weight', weight ?? null);
	if (status) animal.set('status', status);
	if (reproductiveStatus) animal.set('reproductiveStatus', reproductiveStatus);
	if (fatherId !== undefined) animal.set('fatherId', fatherId ? decodeId(fatherId) : null);
	if (motherId !== undefined) animal.set('motherId', motherId ? decodeId(motherId) : null);
	if (acquisitionType) animal.set('acquisitionType', acquisitionType);
	if (acquisitionDate) animal.set('acquisitionDate', new Date(acquisitionDate));

	// Validate parent sex
	let father: Animal | null = null;
	let mother: Animal | null = null;
	const fatherIdDecoded = fatherId ? decodeId(fatherId) : null;
	const motherIdDecoded = motherId ? decodeId(motherId) : null;
	if (fatherIdDecoded) father = await Animal.findByPk(fatherIdDecoded);
	if (motherIdDecoded) mother = await Animal.findByPk(motherIdDecoded);
	const parentSexError = validateParentSex(father, mother);
	if (parentSexError) {
		return reply.code(400).send({ message: parentSexError });
	}

	await animal.save();

	// Create or update weight measurement if weight is provided
	if (weight !== undefined && weight !== null) {
		await AnimalMeasurement.create({
			animalId: animal.id,
			measurementType: 'weight',
			value: weight,
			unit: 'kg',
			measuredAt: new Date(),
			measuredBy: request.user?.id || null,
			method: 'update',
			notes: 'Weight updated',
		});
	}

	// Reload the animal with associations
	const animalWithAssociations = await findAnimalById(id);
	reply.send(serializeAnimal(animalWithAssociations!, request?.language || 'en'));
};

export const deleteAnimal = async (request: FastifyRequest<AnimalDeleteRoute>, reply: FastifyReply) => {
	const { id } = request.params;
	const animal = await findAnimalById(id);
	if (!animal) {
		return reply.code(404).send({ message: 'Animal not found' });
	}
	await animal.destroy();
	reply.send({ message: 'Animal deleted (soft)' });
};
