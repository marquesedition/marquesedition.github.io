import { readFile } from "node:fs/promises";
import { defineCollection, z } from "astro:content";

const readJson = async <T>(relativePath: string): Promise<T> => {
  const file = await readFile(new URL(relativePath, import.meta.url), "utf-8");
  return JSON.parse(file) as T;
};

const reels = defineCollection({
  loader: async () => {
    const payload = await readJson<{
      reels: Array<Record<string, unknown>>;
    }>("./data/reels.json");

    return payload.reels.map((reel) => ({
      id: String(reel.shortcode),
      ...reel,
    }));
  },
  schema: z.object({
    shortcode: z.string(),
    url: z.string().url(),
    date: z.string(),
    timestamp: z.number(),
    thumbnail_url: z.string().optional(),
    view_count: z.number().optional(),
    title: z.string(),
    summary: z.string(),
    label: z.string(),
    caption: z.string().optional(),
  }),
});

const reelsMeta = defineCollection({
  loader: async () => {
    const payload = await readJson<{
      generated_at: string;
      source_profile: string;
      source_url: string;
      profile: {
        username: string;
        full_name: string;
        category: string;
        bio: string;
        followers: number;
        following: number;
        posts: number;
        highlights: number;
      };
    }>("./data/reels.json");

    return [
      {
        id: "profile",
        generatedAt: payload.generated_at,
        sourceProfile: payload.source_profile,
        sourceUrl: payload.source_url,
        profile: payload.profile,
      },
    ];
  },
  schema: z.object({
    generatedAt: z.string(),
    sourceProfile: z.string(),
    sourceUrl: z.string().url(),
    profile: z.object({
      username: z.string(),
      full_name: z.string(),
      category: z.string(),
      bio: z.string(),
      followers: z.number(),
      following: z.number(),
      posts: z.number(),
      highlights: z.number(),
    }),
  }),
});

const streams = defineCollection({
  loader: async () => {
    const payload = await readJson<{
      streams: Array<Record<string, unknown>>;
    }>("./data/streams.json");

    return payload.streams.map((stream, index) => ({
      id: String(stream.video_id),
      order: index,
      ...stream,
    }));
  },
  schema: z.object({
    order: z.number(),
    video_id: z.string(),
    url: z.string().url(),
    embed_url: z.string().url(),
    title: z.string(),
    summary: z.string(),
    published_text: z.string(),
    view_count_text: z.string(),
    duration: z.string(),
    label: z.string(),
    status: z.string(),
    thumbnail_url: z.string().url(),
    embeddable: z.boolean(),
    embed_error: z.string().optional(),
  }),
});

const streamsMeta = defineCollection({
  loader: async () => {
    const payload = await readJson<{
      generated_at: string;
      source_profile: string;
      source_url: string;
      profile: {
        handle: string;
        title: string;
        channel_id: string;
        channel_url: string;
        source_url: string;
        subscribers: number;
        videos: number;
      };
    }>("./data/streams.json");

    return [
      {
        id: "profile",
        generatedAt: payload.generated_at,
        sourceProfile: payload.source_profile,
        sourceUrl: payload.source_url,
        profile: payload.profile,
      },
    ];
  },
  schema: z.object({
    generatedAt: z.string(),
    sourceProfile: z.string(),
    sourceUrl: z.string().url(),
    profile: z.object({
      handle: z.string(),
      title: z.string(),
      channel_id: z.string(),
      channel_url: z.string().url(),
      source_url: z.string().url(),
      subscribers: z.number(),
      videos: z.number(),
    }),
  }),
});

const events = defineCollection({
  loader: async () => {
    const payload = await readJson<{
      events: Array<Record<string, unknown>>;
    }>("./data/events.json");

    return payload.events.map((event, index) => ({
      id: `${String(event.month_id)}-${index}`,
      order: index,
      ...event,
    }));
  },
  schema: z.object({
    order: z.number(),
    month_id: z.string(),
    month_label: z.string().optional(),
    date_label: z.string(),
    artist: z.string().optional(),
    location: z.string(),
    venue: z.string(),
    offers: z
      .array(
        z.object({
          label: z.string(),
          url: z.string().url(),
        }),
      )
      .optional(),
  }),
});

const eventsMeta = defineCollection({
  loader: async () => {
    const payload = await readJson<{
      generated_at?: string;
      source: string;
      source_url: string;
      artist: string;
      featured_residency?: {
        title: string;
        venue: string;
        location: string;
        area?: string;
        address: string;
        schedule_label: string;
        time_label: string;
        map_url: string;
        venue_url: string;
      };
    }>("./data/events.json");

    return [
      {
        id: "meta",
        generatedAt: payload.generated_at ?? "",
        source: payload.source,
        sourceUrl: payload.source_url,
        artist: payload.artist,
        featuredResidency: payload.featured_residency,
      },
    ];
  },
  schema: z.object({
    generatedAt: z.string(),
    source: z.string(),
    sourceUrl: z.string().url(),
    artist: z.string(),
    featuredResidency: z
      .object({
        title: z.string(),
        venue: z.string(),
        location: z.string(),
        area: z.string().optional(),
        address: z.string(),
        schedule_label: z.string(),
        time_label: z.string(),
        map_url: z.string().url(),
        venue_url: z.string().url(),
      })
      .optional(),
  }),
});

export const collections = {
  reels,
  reelsMeta,
  streams,
  streamsMeta,
  events,
  eventsMeta,
};
