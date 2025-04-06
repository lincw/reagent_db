namespace :db do
  desc "Analyze database contents related to MGC2752"
  task analyze_gene_data: :environment do
    puts "Database analysis for gene mapping issue:"
    
    # Check if we have the human_genes table
    if ActiveRecord::Base.connection.table_exists?('human_genes')
      puts "1. human_genes table exists"
      puts "2. human_genes column names: #{HumanGene.column_names.join(', ')}"
      
      # Check for MGC2752 in original_name
      mgc_genes = HumanGene.where("original_name LIKE ?", "%MGC2752%")
      puts "3. Found #{mgc_genes.count} records with MGC2752 in original_name"
      mgc_genes.each do |gene|
        puts "   - ID: #{gene.id}, HGNC: #{gene.hgnc_symbol}, Original: #{gene.original_name}"
      end
      
      # Check for CENPBD2P
      cenpbd_genes = HumanGene.where("hgnc_symbol = ?", "CENPBD2P")
      puts "4. Found #{cenpbd_genes.count} records with HGNC symbol CENPBD2P"
      cenpbd_genes.each do |gene|
        puts "   - ID: #{gene.id}, HGNC: #{gene.hgnc_symbol}, Original: #{gene.original_name}"
      end
    else
      puts "human_genes table does not exist"
    end
    
    # Check sequences with MGC2752 in the name
    if ActiveRecord::Base.connection.table_exists?('sequences')
      mgc_sequences = Sequence.where("name LIKE ?", "%MGC2752%")
      puts "5. Found #{mgc_sequences.count} sequences with MGC2752 in name"
      mgc_sequences.each do |seq|
        puts "   - ID: #{seq.id}, Name: #{seq.name}"
        puts "   - Gene symbol result: #{find_gene_symbol(seq, seq.name)}" if defined?(find_gene_symbol)
      end
    end
    
    puts "\nPlease run a BLAST search with query that would match MGC2752 and check the results."
  end
end
