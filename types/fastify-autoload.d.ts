declare module '@fastify/autoload' {
  import { FastifyPluginAsync } from 'fastify';

  interface AutoloadOptions {
    dir: string;
    matchFilter?: (path: string) => boolean;
    options?: {
      prefix?: string;
    };
  }

  const fastifyAutoload: FastifyPluginAsync<AutoloadOptions>;
  export default fastifyAutoload;
}
