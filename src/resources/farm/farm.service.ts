import { Database } from '../../database';
import { FarmMemberWithFarm } from '../farm-member/farm-member.schema';
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
		try {
			const farmMembers = await this.db.models.FarmMember.findAll({
				where: { userId },
				include: [{
					model: FarmModel,
					as: 'farm',
					required: true,
				}],
			}) as FarmMemberWithFarm[];

			return farmMembers.map(member => member.farm);
		} catch (error) {
			console.error('Error fetching farms for user:', userId, error);
			throw new Error('Failed to fetch farms');
		}
	}

}
