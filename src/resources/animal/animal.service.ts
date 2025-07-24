import { BaseService } from '../../services/base.service';
import { AnimalModel } from './animal.model';
import { AnimalCreate } from './animal.schema';
import { decodeId } from '../../utils/id-hash-util';

export class AnimalService extends BaseService {

	async getAnimals(farmId: number): Promise<AnimalModel[] | null> {
		return this.db.models.Animal.findAll({
			where: {
				farmId: farmId,
			},
		});
	}

	async createAnimal({ data }:{ data: AnimalCreate & {farmId: number} }): Promise<AnimalModel | null> {

		const { breedId, speciesId, fatherId, motherId } = await this.decodeAnimalIds(data);
		return this.db.models.Animal.create({ ...data, breedId, speciesId, fatherId, motherId });
	}

	async decodeAnimalIds(ids: {breedId: string, speciesId: string, fatherId?: string | undefined, motherId? : string  | undefined})  {
		return {
			breedId: decodeId(ids.breedId)!,
			speciesId: decodeId(ids.speciesId)!,
			fatherId: ids.fatherId ? decodeId(ids.fatherId) : undefined,
			motherId: ids.motherId ? decodeId(ids.motherId) : undefined,
		};
	}
}
