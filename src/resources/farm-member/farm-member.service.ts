import { BaseService } from '../../services/base.service';
import { FarmMemberModel } from './farm-member.model';
import { FarmMemberCreateInput, FarmMemberWithUser } from './farm-member.schema';
import { PaginatedResult, PaginationParams } from '../../utils/pagination';

export class FarmMemberService extends BaseService {

	async createFarmMember(data: FarmMemberCreateInput): Promise<FarmMemberModel> {
		const farmMember = await this.db.models.FarmMember.create(data);
		return farmMember;
	}

	async getFarmMembersWithUsers(farmId: number, pagination: PaginationParams): Promise<PaginatedResult<FarmMemberWithUser>> {
		const findOptions = {
			where: { farmId },
			include: [{
				model: this.db.models.User,
				as: 'user',
				attributes: ['id', 'displayName', 'email'],
			}],
		};

		const { rows, count } = await this.db.models.FarmMember.findAndCountAll({
			...findOptions,
			limit: pagination.limit,
			offset: pagination.offset,
			distinct: true,
		});

		return {
			rows: rows as unknown as FarmMemberWithUser[],
			pagination: {
				page: pagination.page,
				limit: pagination.limit,
				total: count,
				totalPages: Math.ceil(count / pagination.limit),
			},
		};
	}
}
