import { Database } from '../../database';
import { FarmMemberModel } from '../farm-member/farm-member.model';
import { FarmModel } from './farm.model';
import { FarmCreateInput } from './farm.schema';

export class FarmService {
	private db: Database;

	constructor(db: Database) {
		this.db = db;
	}

	async createFarm(data: FarmCreateInput): Promise<FarmModel> {
		const farm = await this.db.models.Farm.create(data);
		return farm;
	}

	async getFarms(userId: number): Promise<FarmModel[]> {
		const farms = await this.db.models.Farm.findAll({
			include: [{
				model: FarmMemberModel,
				as: 'members',
				where: {
					userId,
				},
				required: true,
			}],
		});
		return farms;
	}

}
