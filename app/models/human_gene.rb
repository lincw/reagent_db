class HumanGene < ApplicationRecord
  has_many :sequences, dependent: :nullify
  
  # Find the HGNC symbol for a given original gene name
  def self.find_hgnc_for_original_name(original_name)
    return nil if original_name.blank?
    
    gene = find_by("lower(original_name) = ?", original_name.downcase)
    gene&.hgnc_symbol
  end
end
