import { createHash } from 'node:crypto';
import { createReadStream, createWriteStream } from 'node:fs';
import {
  access,
  mkdir,
  mkdtemp,
  readFile,
  rename,
  rm,
} from 'node:fs/promises';
import { dirname, isAbsolute, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';

const appRoot = fileURLToPath(new URL('..', import.meta.url));
const release = JSON.parse(
  await readFile(new URL('../presentation-data-release.json', import.meta.url), 'utf8'),
);
const outputDirectory = resolve(
  appRoot,
  process.env.PRESENTATION_DATA_DIR ?? 'public/data/v1',
);
const outputRelativePath = relative(appRoot, outputDirectory);
const shardPathPattern = /^\/data\/v1\/uf\/[A-Z]{2}(?:-\d{3})?\.json$/;

if (outputRelativePath.startsWith('..') || isAbsolute(outputRelativePath)) {
  throw new Error('PRESENTATION_DATA_DIR precisa permanecer dentro de app/.');
}

async function exists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function validatePresentationData(directory) {
  const metadata = JSON.parse(
    await readFile(resolve(directory, 'metadata.json'), 'utf8'),
  );
  const index = JSON.parse(
    await readFile(resolve(directory, 'municipal-index.json'), 'utf8'),
  );

  if (
    metadata.schema_version !== release.schemaVersion ||
    index.schema_version !== release.schemaVersion
  ) {
    throw new Error('O artefato de dados diverge da versão de contrato configurada.');
  }
  if (
    metadata.territorial_universe?.id !== release.territorialUniverse ||
    index.territorial_universe !== release.territorialUniverse
  ) {
    throw new Error('O universo territorial do artefato é inesperado.');
  }
  if (
    metadata.territorial_universe?.municipality_count !==
      release.municipalityCount ||
    index.municipalities?.length !== release.municipalityCount
  ) {
    throw new Error('A quantidade de localidades do artefato é inesperada.');
  }

  const codes = new Set();
  const shards = new Set();
  for (const municipality of index.municipalities) {
    if (
      typeof municipality.codigo_ibge !== 'string' ||
      codes.has(municipality.codigo_ibge) ||
      typeof municipality.shard !== 'string' ||
      !shardPathPattern.test(municipality.shard)
    ) {
      throw new Error('O índice municipal do artefato é inválido.');
    }
    codes.add(municipality.codigo_ibge);
    shards.add(municipality.shard);
  }

  await Promise.all(
    [...shards].map((shard) => access(resolve(directory, shard.slice(9)))),
  );
}

async function sha256(path) {
  const hash = createHash('sha256');
  await pipeline(createReadStream(path), hash);
  return hash.digest('hex');
}

async function hydrate() {
  const metadataPath = resolve(outputDirectory, 'metadata.json');
  const indexPath = resolve(outputDirectory, 'municipal-index.json');
  if ((await exists(metadataPath)) && (await exists(indexPath))) {
    await validatePresentationData(outputDirectory);
    console.log('Dados de apresentação v1 já estão materializados e válidos.');
    return;
  }

  const outputParent = dirname(outputDirectory);
  await mkdir(outputParent, { recursive: true });
  const temporaryRoot = await mkdtemp(
    resolve(outputParent, '.antes-da-chuva-presentation-'),
  );
  const archivePath = resolve(temporaryRoot, 'presentation-data-v1.tar.gz');
  const extractedDirectory = resolve(temporaryRoot, 'v1');

  try {
    console.log(`Baixando dados de apresentação: ${release.archiveUrl}`);
    const response = await fetch(release.archiveUrl, {
      headers: { 'User-Agent': 'antes-da-chuva-build/1.0' },
      redirect: 'follow',
    });
    if (!response.ok || !response.body) {
      throw new Error(
        `Falha ao baixar os dados de apresentação: HTTP ${response.status}`,
      );
    }
    await pipeline(Readable.fromWeb(response.body), createWriteStream(archivePath));

    const archiveHash = await sha256(archivePath);
    if (archiveHash !== release.sha256) {
      throw new Error(
        `SHA-256 do artefato inválido: esperado ${release.sha256}, recebido ${archiveHash}`,
      );
    }

    await mkdir(extractedDirectory);
    const extraction = spawnSync(
      'tar',
      ['-xzf', archivePath, '-C', extractedDirectory],
      { encoding: 'utf8' },
    );
    if (extraction.status !== 0) {
      throw new Error(
        `Falha ao extrair os dados de apresentação: ${extraction.stderr || extraction.stdout}`,
      );
    }

    await validatePresentationData(extractedDirectory);
    await rm(outputDirectory, { recursive: true, force: true });
    await rename(extractedDirectory, outputDirectory);
    console.log(
      `Dados de apresentação v1 materializados para ${release.municipalityCount} localidades.`,
    );
  } finally {
    await rm(temporaryRoot, { recursive: true, force: true });
  }
}

await hydrate();
