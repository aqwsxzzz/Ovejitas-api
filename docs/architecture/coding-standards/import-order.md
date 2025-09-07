# Import Order

```typescript
// 1. External libraries
import { FastifyInstance } from 'fastify';
import { Type, Static } from '@sinclair/typebox';

// 2. Utils
import { createPostEndpointSchema } from '../../utils/schema-builder';
import { encodeId, decodeId } from '../../utils/id-hash-util';

// 3. Related resources (if needed)
import { RelatedResourceResponse } from '../related/related.schema';

// 4. Local files
import { ResourceModel } from './resource.model';
```
