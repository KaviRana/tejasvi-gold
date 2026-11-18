import { defineCollection, z } from "astro:content";
import { file } from "astro/loaders";
import categoryList from "./data/categories.json";
import attributes from "./data/attributes.json";

// Every design is checked at build time. A missing field, a bad code, an unknown
// category or weight_min > weight_max stops the build, so a broken catalogue never goes live.
const categoryIds = categoryList.map((c) => c.id) as [string, ...string[]];

const designs = defineCollection({
  loader: file("src/data/designs.json"),
  schema: z
    .object({
      id: z.string().regex(/^TG-\d{3,4}$/, "code must look like TG-001"),
      category: z.enum(categoryIds),
      purity: z.enum(["22K", "18K"]).default("22K"),
      weight_min_g: z.number().positive(),
      weight_max_g: z.number().positive(),
      status: z.enum(["in-stock", "on-approval", "made-to-order"]),
      dispatch_days: z.string().regex(/^\d+(-\d+)?$/).optional(),
      added: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
      image: z.string().startsWith("/designs/").optional(), // default: /designs/<id>.jpg
      sample: z.boolean().optional(),
    })
    .refine((d) => d.weight_min_g <= d.weight_max_g, { message: "weight_min_g must be <= weight_max_g" }),
});

const categories = defineCollection({
  loader: file("src/data/categories.json"),
  schema: z.object({ id: z.string(), name: z.string(), one: z.string(), single: z.string(), noun: z.string(), order: z.number().int() }),
});

// Tags come from tools/data/tags_review.csv (only rows marked "checked"), via scripts/apply-tags.mjs.
// Each value must be one of the fixed lists in src/data/attributes.json.
const list = (k: keyof typeof attributes) => z.enum(attributes[k] as [string, ...string[]]);
const tags = defineCollection({
  loader: file("src/data/tags.json"),
  schema: z.object({ id: z.string().regex(/^TG-\d{3,4}$/), name: z.string().optional(), motif: list("motif"), finish: list("finish"), work: list("work"), stones: list("stones"), occasion: list("occasion") }),
});

export const collections = { designs, categories, tags };
