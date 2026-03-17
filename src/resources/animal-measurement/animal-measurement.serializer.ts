import { encodeId } from '../../utils/id-hash-util';
import { AnimalMeasurementResponse, AnimalMeasurementWithDeltaResponse } from './animal-measurement.schema';
import { AnimalMeasurementModel } from './animal-measurement.model';

export class AnimalMeasurementSerializer {
	static serialize(measurement: AnimalMeasurementModel): AnimalMeasurementResponse {
		return {
			id: encodeId(measurement.id),
			animalId: encodeId(measurement.animalId),
			measurementType: measurement.measurementType,
			value: measurement.value,
			unit: measurement.unit,
			measuredAt: measurement.measuredAt,
			measuredBy: encodeId(measurement.measuredBy),
			notes: measurement.notes,
			createdAt: measurement.createdAt,
			updatedAt: measurement.updatedAt,
		};
	}

	static serializeMany(measurements: AnimalMeasurementModel[]): AnimalMeasurementResponse[] {
		return measurements.map(m => this.serialize(m));
	}

	static serializeManyWithDeltas(measurements: AnimalMeasurementModel[]): AnimalMeasurementWithDeltaResponse[] {
		// Sort chronologically (oldest first) to compute deltas forward
		const sorted = [...measurements].sort(
			(a, b) => new Date(a.measuredAt).getTime() - new Date(b.measuredAt).getTime(),
		);

		const withDeltas: AnimalMeasurementWithDeltaResponse[] = sorted.map((measurement, index) => {
			const base = this.serialize(measurement);
			if (index === 0) {
				return { ...base, change: null, changePercent: null };
			}

			const previousValue = sorted[index - 1]!.value;
			const change = Number((measurement.value - previousValue).toFixed(2));
			const changePercent = previousValue !== 0
				? Number((((measurement.value - previousValue) / previousValue) * 100).toFixed(2))
				: null;

			return { ...base, change, changePercent };
		});

		// Reverse back to DESC order (newest first) to match the API response order
		return withDeltas.reverse();
	}
}
