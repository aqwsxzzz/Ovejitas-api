export const animalMeasurementCreateSchema = {
  body: {
    type: "object",
    required: ["measurementType", "value", "unit"],
    properties: {
      measurementType: { 
        type: "string", 
        enum: ["weight", "height", "body_condition"] 
      },
      value: { 
        type: "number", 
        minimum: 0 
      },
      unit: { 
        type: "string", 
        minLength: 1,
        maxLength: 10 
      },
      measuredAt: { 
        type: "string", 
        format: "date-time" 
      },
      method: { 
        type: "string", 
        maxLength: 50 
      },
      notes: { 
        type: "string" 
      },
    },
    additionalProperties: false,
  },
  params: {
    type: "object",
    required: ["farmId", "animalId"],
    properties: {
      farmId: { type: "string", minLength: 1 },
      animalId: { type: "string", minLength: 1 },
    },
    additionalProperties: false,
  },
};

export const animalMeasurementUpdateSchema = {
  body: {
    type: "object",
    properties: {
      value: { 
        type: "number", 
        minimum: 0 
      },
      unit: { 
        type: "string", 
        minLength: 1,
        maxLength: 10 
      },
      measuredAt: { 
        type: "string", 
        format: "date-time" 
      },
      method: { 
        type: "string", 
        maxLength: 50 
      },
      notes: { 
        type: "string" 
      },
    },
    additionalProperties: false,
  },
  params: {
    type: "object",
    required: ["farmId", "animalId", "measurementId"],
    properties: {
      farmId: { type: "string", minLength: 1 },
      animalId: { type: "string", minLength: 1 },
      measurementId: { type: "string", minLength: 1 },
    },
    additionalProperties: false,
  },
};

export const animalMeasurementListSchema = {
  params: {
    type: "object",
    required: ["farmId", "animalId"],
    properties: {
      farmId: { type: "string", minLength: 1 },
      animalId: { type: "string", minLength: 1 },
    },
    additionalProperties: false,
  },
  querystring: {
    type: "object",
    properties: {
      measurementType: { 
        type: "string", 
        enum: ["weight", "height", "body_condition"] 
      },
      startDate: { 
        type: "string", 
        format: "date-time" 
      },
      endDate: { 
        type: "string", 
        format: "date-time" 
      },
      limit: { 
        type: "integer", 
        minimum: 1, 
        maximum: 1000,
        default: 100 
      },
    },
    additionalProperties: false,
  },
};

export const animalMeasurementGetSchema = {
  params: {
    type: "object",
    required: ["farmId", "animalId", "measurementId"],
    properties: {
      farmId: { type: "string", minLength: 1 },
      animalId: { type: "string", minLength: 1 },
      measurementId: { type: "string", minLength: 1 },
    },
    additionalProperties: false,
  },
};