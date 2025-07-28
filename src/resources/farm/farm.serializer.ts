import { encodeId } from '../../utils/id-hash-util';
import { FarmModel } from './farm.model';
import { FarmResponse } from './farm.schema';

export class FarmSerializer {
	static serialize(farm: FarmModel): FarmResponse {
		return {
			id: encodeId((farm.dataValues.id)),
			name: farm.dataValues.name,
			createdAt: farm.dataValues.createdAt,
			updatedAt: farm.dataValues.updatedAt,
		};
	}

	static serializeMany(farms: FarmModel[]): FarmResponse[] {
		return farms.map(farm => this.serialize(farm));
	}
}
