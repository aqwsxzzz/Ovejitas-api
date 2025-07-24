import { BaseService } from '../../services/base.service';
import { isBreedNameUniqueForSpecies } from './breed.helper';
import { BreedModel } from './breed.model';

export class BreedService extends BaseService {

	async createBreed({ name, speciesId }:{ name: string, speciesId: number }): Promise<BreedModel> {
		const isUnique = await isBreedNameUniqueForSpecies(name, speciesId, this.db);

		if (!isUnique) {
			throw new Error('Breed name must be unique per species.');
		}

		return await this.db.models.Breed.create({ name, speciesId });
	}
}
