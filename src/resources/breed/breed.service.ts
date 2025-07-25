import { BreedUpdate } from './breed.schema';
import { BaseService } from '../../services/base.service';
import { BreedModel } from './breed.model';
import { OrderParser, TypedOrderConfig } from '../../utils/order-parser';
import { FindOptions } from 'sequelize';

export class BreedService extends BaseService {

	private static readonly ALLOWED_ORDERS = OrderParser.createConfig({
		name: {
			attribute: 'name',
		},
		id: {
			attribute: 'id',
		},
		createdAt: {
			attribute: 'createdAt',
		},
	} satisfies TypedOrderConfig);

	async createBreed({ name, speciesId }:{ name: string, speciesId: number }): Promise<BreedModel> {
		return await this.db.models.Breed.create({ name, speciesId });
	}

	async getBreedsBySpecies(speciesId: number, order?: string): Promise<BreedModel[]> {
		const findOptions: FindOptions = {
			where: { speciesId },
		};

		if (order) {
			this.validateOrder(order, BreedService.ALLOWED_ORDERS);
			findOptions.order = this.parseOrder(order, BreedService.ALLOWED_ORDERS);
		} else {
			// Default order by name ASC
			findOptions.order = [['name', 'ASC']];
		}

		return await this.db.models.Breed.findAll(findOptions);
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
