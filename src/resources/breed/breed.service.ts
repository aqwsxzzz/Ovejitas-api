import { BreedUpdate } from './breed.schema';
import { BaseService } from '../../services/base.service';
import { BreedModel } from './breed.model';

export class BreedService extends BaseService {

	async createBreed({ name, speciesId }:{ name: string, speciesId: number }): Promise<BreedModel> {
		return await this.db.models.Breed.create({ name, speciesId });
	}

	async updateBreed(id: number, data: BreedUpdate): Promise<BreedModel> {

		const [affectedCount] = await this.db.models.Breed.update(data, {
			where: { id },
		});

		if (affectedCount === 0) {
			throw new Error('Breed not found');
		}

		const updatedBreed = await this.db.models.Breed.findByPk(id);
		if (!updatedBreed) {
			throw new Error('Breed not found after update');
		}

		return updatedBreed;

	}
}
