import api from './api'
import type { ParsedIngredient, ProductMatch, Recipe } from '../types'

interface ParseUrlResponse {
  title?: string
  ingredients: string[]
  parsed_ingredients: ParsedIngredient[]
  source_url: string
}

interface ParseTextResponse {
  parsed_ingredients: ParsedIngredient[]
}

interface MatchProductsResponse {
  matches: ProductMatch[]
  not_found: ParsedIngredient[]
  needs_review_count?: number
  high_confidence_count?: number
  total_ingredients?: number
  matched_count?: number
}

interface AddToCartResponse {
  added: number
  failed: number
  cart: unknown
}

export async function parseRecipeUrl(url: string): Promise<ParseUrlResponse> {
  const response = await api.post('/recipes/parse-url', { url })
  return response.data
}

export async function parseIngredientText(text: string): Promise<ParseTextResponse> {
  const response = await api.post('/recipes/parse-text', { text })
  return response.data
}

export async function matchProductsToIngredients(
  ingredients: ParsedIngredient[]
): Promise<MatchProductsResponse> {
  const response = await api.post('/recipes/match-products', { ingredients })
  return response.data
}

export async function addMatchedToCart(
  matches: ProductMatch[]
): Promise<AddToCartResponse> {
  const response = await api.post('/recipes/add-to-cart', { matches })
  return response.data
}

export async function getRecipeHistory(limit = 20): Promise<{ recipes: Recipe[] }> {
  const response = await api.get(`/recipes/history?limit=${limit}`)
  return response.data
}
