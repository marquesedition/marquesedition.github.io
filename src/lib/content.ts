import { getCollection, getEntry } from "astro:content";

export const getReelsData = async () => {
  const [reelEntries, metaEntry] = await Promise.all([
    getCollection("reels"),
    getEntry("reelsMeta", "profile"),
  ]);

  const reels = reelEntries.map((entry) => entry.data).sort((a, b) => b.timestamp - a.timestamp);

  return {
    reels,
    generatedAt: metaEntry?.data.generatedAt ?? "",
    sourceUrl: metaEntry?.data.sourceUrl ?? "",
    sourceProfile: metaEntry?.data.sourceProfile ?? "",
    profile:
      metaEntry?.data.profile ?? {
        username: "",
        full_name: "",
        category: "",
        bio: "",
        followers: 0,
        following: 0,
        posts: 0,
        highlights: 0,
      },
  };
};

export const getStreamsData = async () => {
  const [streamEntries, metaEntry] = await Promise.all([
    getCollection("streams"),
    getEntry("streamsMeta", "profile"),
  ]);

  const streams = streamEntries.map((entry) => entry.data).sort((a, b) => a.order - b.order);

  return {
    streams,
    generatedAt: metaEntry?.data.generatedAt ?? "",
    sourceUrl: metaEntry?.data.sourceUrl ?? "",
    sourceProfile: metaEntry?.data.sourceProfile ?? "",
    profile:
      metaEntry?.data.profile ?? {
        handle: "",
        title: "",
        channel_id: "",
        channel_url: "",
        source_url: "",
        subscribers: 0,
        videos: 0,
      },
  };
};

export const getEventsData = async () => {
  const [eventEntries, metaEntry] = await Promise.all([
    getCollection("events"),
    getEntry("eventsMeta", "meta"),
  ]);

  const events = eventEntries.map((entry) => entry.data).sort((a, b) => a.order - b.order);

  return {
    events,
    generatedAt: metaEntry?.data.generatedAt ?? "",
    source: metaEntry?.data.source ?? "",
    sourceUrl: metaEntry?.data.sourceUrl ?? "",
    artist: metaEntry?.data.artist ?? "",
    featuredResidency: metaEntry?.data.featuredResidency,
  };
};
