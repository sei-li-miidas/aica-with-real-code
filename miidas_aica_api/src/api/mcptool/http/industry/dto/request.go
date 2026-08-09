package dto

type SearchSemanticIndustryRequest struct {
	Sentence string   `json:"Sentence"`
	Provider *string  `json:"Provider"`
	Distance *float64 `json:"Distance"`
	Limit    *uint    `json:"Limit"`
}
