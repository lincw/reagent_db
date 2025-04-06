class Sequence < ApplicationRecord
  # Conditionally include human_gene association if the table exists
  if ActiveRecord::Base.connection.table_exists?('human_genes')
    belongs_to :human_gene, optional: true
  end

  # Method to get gene symbol regardless of database structure
  def gene_symbol
    if defined?(human_gene) && human_gene.present?
      human_gene.hgnc_symbol
    elsif respond_to?(:gene_name) && gene_name.present?
      gene_name
    elsif name.present? && name.match?(/^[A-Z0-9]+$/)
      # If name looks like a gene symbol (all caps)
      name
    else
      nil
    end
  end
end