AccessTypeDict = {
    "@graph": [
        {
            "@id": "dandi:AccessType",
            "@type": "rdfs:Class",
            "rdfs:comment": "An enumeration of access status options",
            "rdfs:label": "Access status type",
            "rdfs:subClassOf": {"@id": "schema:Enumeration"},
        },
        {
            "@id": "dandi:OpenAccess",
            "@type": "dandi:AccessType",
            "rdfs:comment": "The dandiset is openly accessible",
            "rdfs:label": "Open access",
        },
        {
            "@id": "dandi:EmbargoedAccess",
            "@type": "dandi:AccessType",
            "rdfs:comment": "The dandiset is embargoed",
            "rdfs:label": "Embargoed",
        },
        {
            "@id": "dandi:RestrictedAccess",
            "@type": "dandi:AccessType",
            "rdfs:comment": "The dandiset is restricted",
            "rdfs:label": "Restricted",
        },
    ]
}

DigestTypeDict = {
    "@graph": [
        {
            "@id": "dandi:DigestType",
            "@type": "rdfs:Class",
            "rdfs:comment": "An enumeration of checksum types",
            "rdfs:label": "Checksum Type",
            "rdfs:subClassOf": {"@id": "schema:Enumeration"},
        },
        {
            "@id": "dandi:md5",
            "@type": "dandi:DigestType",
            "rdfs:comment": "MD5 checksum",
            "rdfs:label": "MD5",
        },
        {
            "@id": "dandi:sha1",
            "@type": "dandi:DigestType",
            "rdfs:comment": "SHA1 checksum",
            "rdfs:label": "SHA1",
        },
        {
            "@id": "dandi:sha2-256",
            "@type": "dandi:DigestType",
            "rdfs:comment": "SHA2-256 checksum",
            "rdfs:label": "SHA2-256",
        },
        {
            "@id": "dandi:sha3-256",
            "@type": "dandi:DigestType",
            "rdfs:comment": "SHA3-256 checksum",
            "rdfs:label": "SHA3-256",
        },
        {
            "@id": "dandi:blake2b-256",
            "@type": "dandi:DigestType",
            "rdfs:comment": "BLAKE2B-256 checksum",
            "rdfs:label": "BLAKE2B-256",
        },
        {
            "@id": "dandi:blake3",
            "@type": "dandi:DigestType",
            "rdfs:comment": "BLAKE3-256 checksum",
            "rdfs:label": "BLAKE3-256",
        },
        {
            "@id": "dandi:dandi-etag",
            "@type": "dandi:DigestType",
            "rdfs:comment": "S3-style ETag",
            "rdfs:label": "DANDI ETag",
        },
    ]
}

IdentifierTypeDict = {
    "@graph": [
        {
            "@id": "dandi:IdentifierType",
            "@type": "rdfs:Class",
            "rdfs:comment": "An enumeration of identifiers",
            "rdfs:label": "License type",
            "rdfs:subClassOf": {"@id": "schema:Enumeration"},
        },
        {
            "@id": "dandi:doi",
            "sameAs": "idorg:doi",
            "@type": "dandi:IdentifierType",
            "rdfs:label": "DOI",
        },
        {
            "@id": "dandi:orcid",
            "sameAs": "idorg:orcid",
            "@type": "dandi:IdentifierType",
            "rdfs:label": "ORCID",
        },
        {
            "@id": "dandi:ror",
            "sameAs": "https://ror.org/",
            "@type": "dandi:IdentifierType",
            "rdfs:label": "ROR",
        },
        {
            "@id": "dandi:dandi",
            "sameAs": "idorg:dandi",
            "@type": "dandi:IdentifierType",
            "rdfs:label": "DANDI",
        },
        {
            "@id": "dandi:rrid",
            "sameAs": "idorg:rrid",
            "@type": "dandi:IdentifierType",
            "rdfs:label": "RRID",
        },
    ]
}
LicenseTypeDict = {
    "@graph": [
        {
            "@id": "dandi:LicenseType",
            "@type": "rdfs:Class",
            "rdfs:comment": "An enumeration of supported licenses",
            "rdfs:label": "License type",
            "rdfs:subClassOf": {"@id": "schema:Enumeration"},
        },
        {
            "@id": "spdx:CC0-1.0",
            "rdfs:seeAlso": "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
            "@type": "dandi:LicenseType",
            "rdfs:label": "CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        },
        {
            "@id": "spdx:CC-BY-4.0",
            "rdfs:seeAlso": "https://creativecommons.org/licenses/by/4.0/legalcode",
            "@type": "dandi:LicenseType",
            "rdfs:label": "Attribution 4.0 International (CC BY 4.0)",
        },
    ]
}

RelationTypeDict = {
    "@graph": [
        {
            "@id": "dandi:RelationType",
            "@type": "rdfs:Class",
            "rdfs:comment": "An enumeration of resource relations",
            "rdfs:label": "Resource relation type",
            "rdfs:subClassOf": {"@id": "schema:Enumeration"},
            "prov:wasDerivedFrom": (
                "https://schema.datacite.org/meta/"
                "kernel-4.2/doc/DataCite-MetadataKernel_v4.2.pdf"
            ),
        },
        {
            "@id": "dcite:IsCitedBy",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates that B includes A in a citation",
            "rdfs:label": "IsCitedBy",
        },
        {
            "@id": "dcite:Cites",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates that A includes B in a citation",
            "rdfs:label": "Cites",
        },
        {
            "@id": "dcite:IsSupplementTo",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates that A is a supplement to B",
            "rdfs:label": "IsSupplementTo",
        },
        {
            "@id": "dcite:IsSupplementedBy",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates that B is a supplement to A",
            "rdfs:label": "IsSupplementedBy",
        },
        {
            "@id": "dcite:IsContinuedBy",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is continued by the work B",
            "rdfs:label": "IsContinuedBy",
        },
        {
            "@id": "dcite:Continues",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is a continuation of the work B",
            "rdfs:label": "Continues",
        },
        {
            "@id": "dcite:Describes",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A describes B",
            "rdfs:label": "Describes",
        },
        {
            "@id": "dcite:IsDescribedBy",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is described by B",
            "rdfs:label": "IsDescribedBy",
        },
        {
            "@id": "dcite:HasMetadata",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates resource A has additional metadata B",
            "rdfs:label": "HasMetadata",
        },
        {
            "@id": "dcite:IsMetadataFor",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates additional metadata A for a resource B",
            "rdfs:label": "IsMetadataFor",
        },
        {
            "@id": "dcite:HasVersion",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A has a version (B)",
            "rdfs:label": "HasVersion",
        },
        {
            "@id": "dcite:IsVersionOf",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is a version of B",
            "rdfs:label": "IsVersionOf",
        },
        {
            "@id": "dcite:IsNewVersionOf",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is a new edition of B",
            "rdfs:label": "IsNewVersionOf",
        },
        {
            "@id": "dcite:IsPreviousVersionOf",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is a previous edition of B",
            "rdfs:label": "IsPreviousVersionOf",
        },
        {
            "@id": "dcite:IsPartOf",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is a portion of B",
            "rdfs:label": "IsPartOf",
        },
        {
            "@id": "dcite:HasPart",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A includes the part B",
            "rdfs:label": "HasPart",
        },
        {
            "@id": "dcite:IsReferencedBy",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is used as a source of information by B",
            "rdfs:label": "IsReferencedBy",
        },
        {
            "@id": "dcite:References",
            "@type": "dcite:RelationType",
            "rdfs:comment": "Indicates B is used as a source of information for A",
            "rdfs:label": "References",
        },
        {
            "@id": "dcite:IsDocumentedBy",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates B is documentation about/explaining A",
            "rdfs:label": "IsDocumentedBy",
        },
        {
            "@id": "dcite:Documents",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is documentation about B",
            "rdfs:label": "Documents",
        },
        {
            "@id": "dcite:IsCompiledBy",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates B is used to compile or create A",
            "rdfs:label": "IsCompiledBy",
        },
        {
            "@id": "dcite:Compiles",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates B is the result of a compile or creation event using A",
            "rdfs:label": "Compiles",
        },
        {
            "@id": "dcite:IsVariantFormOf",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is a variant or different form of B",
            "rdfs:label": "IsVariantFormOf",
        },
        {
            "@id": "dcite:IsOriginalFormOf",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is the original form of B",
            "rdfs:label": "IsOriginalFormOf",
        },
        {
            "@id": "dcite:IsIdenticalTo",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates that A is identical to B",
            "rdfs:label": "IsIdenticalTo",
        },
        {
            "@id": "dcite:IsReviewedBy",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates that A is reviewed by B",
            "rdfs:label": "IsReviewedBy",
        },
        {
            "@id": "dcite:Reviews",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates that A is a review of B",
            "rdfs:label": "Reviews",
        },
        {
            "@id": "dcite:IsDerivedFrom",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates B is a source upon which A is based",
            "rdfs:label": "IsDerivedFrom",
        },
        {
            "@id": "dcite:IsSourceOf",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is a source upon which B is based",
            "rdfs:label": "IsSourceOf",
        },
        {
            "@id": "dcite:IsRequiredBy",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is required by B",
            "rdfs:label": "IsRequiredBy",
        },
        {
            "@id": "dcite:Requires",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A requires B",
            "rdfs:label": "Requires",
        },
        {
            "@id": "dcite:Obsoletes",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A replaces B",
            "rdfs:label": "Obsoletes",
        },
        {
            "@id": "dcite:IsObsoletedBy",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is replaced by B",
            "rdfs:label": "IsObsoletedBy",
        },
        {
            "@id": "dcite:IsPublishedIn",
            "@type": "dandi:RelationType",
            "rdfs:comment": "Indicates A is published in B",
            "rdfs:label": "IsPublishedIn",
        },
    ]
}

ParticipantRelationTypeDict = {
    "@graph": [
        {
            "@id": "dandi:ParticipantRelationType",
            "@type": "rdfs:Class",
            "rdfs:comment": "An enumeration of participant relations",
            "rdfs:label": "Participant relation type",
            "rdfs:subClassOf": {"@id": "schema:Enumeration"},
            "prov:wasDerivedFrom": (
                "https://www.ebi.ac.uk/biosamples/docs/guides/relationships"
            ),
        },
        {
            "@id": "dandi:isChildOf",
            "@type": "dandi:ParticipantRelationType",
            "rdfs:comment": "Indicates that A is a child of B",
            "rdfs:label": "Child of",
        },
        {
            "@id": "dandi:isParentOf",
            "@type": "dandi:ParticipantRelationType",
            "rdfs:comment": "Indicates that A is a parent of B",
            "rdfs:label": "Parent of",
        },
        {
            "@id": "dandi:isSiblingOf",
            "@type": "dandi:ParticipantRelationType",
            "rdfs:comment": "Indicates that A is a sibling of B",
            "rdfs:label": "Sibling of",
        },
        {
            "@id": "dandi:isMonozygoticTwinOf",
            "@type": "dandi:ParticipantRelationType",
            "rdfs:comment": "Indicates that A is a monozygotic twin of B",
            "rdfs:label": "Monozygotic twin of",
        },
        {
            "@id": "dandi:isDizygoticTwinOf",
            "@type": "dandi:ParticipantRelationType",
            "rdfs:comment": "Indicates that A is a dizygotic twin of B",
            "rdfs:label": "Dizygotic twin of",
        },
    ]
}

RoleTypeDict = {
    "@graph": [
        {
            "@id": "dandi:RoleType",
            "@type": "rdfs:Class",
            "rdfs:comment": "An enumeration of roles",
            "rdfs:label": "Role Type",
            "rdfs:subClassOf": {"@id": "schema:Enumeration"},
        },
        {
            "@id": "dcite:Author",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Author",
            "rdfs:label": "Author",
        },
        {
            "@id": "dcite:Conceptualization",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Conceptualization",
            "rdfs:label": "Conceptualization",
        },
        {
            "@id": "dcite:ContactPerson",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Contact Person",
            "rdfs:label": "Contact Person",
        },
        {
            "@id": "dcite:DataCollector",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Data Collector",
            "rdfs:label": "Data Collector",
        },
        {
            "@id": "dcite:DataCurator",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Data Curator",
            "rdfs:label": "Data Curator",
        },
        {
            "@id": "dcite:DataManager",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Data Manager",
            "rdfs:label": "Data Manager",
        },
        {
            "@id": "dcite:FormalAnalysis",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Formal Analysis",
            "rdfs:label": "Formal Analysis",
        },
        {
            "@id": "dcite:FundingAcquisition",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Funding Acquisition",
            "rdfs:label": "Funding Acquisition",
        },
        {
            "@id": "dcite:Investigation",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Investigation",
            "rdfs:label": "Investigation",
        },
        {
            "@id": "dcite:Maintainer",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Maintainer",
            "rdfs:label": "Maintainer",
        },
        {
            "@id": "dcite:Methodology",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Methodology",
            "rdfs:label": "Methodology",
        },
        {
            "@id": "dcite:Producer",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Producer",
            "rdfs:label": "Producer",
        },
        {
            "@id": "dcite:ProjectLeader",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Project Leader",
            "rdfs:label": "Project Leader",
        },
        {
            "@id": "dcite:ProjectManager",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Project Manager",
            "rdfs:label": "Project Manager",
        },
        {
            "@id": "dcite:ProjectMember",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Project Member",
            "rdfs:label": "Project Member",
        },
        {
            "@id": "dcite:ProjectAdministration",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Project Administration",
            "rdfs:label": "Project Administration",
        },
        {
            "@id": "dcite:Researcher",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Researcher",
            "rdfs:label": "Researcher",
        },
        {
            "@id": "dcite:Resources",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Resources",
            "rdfs:label": "Resources",
        },
        {
            "@id": "dcite:Software",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Software",
            "rdfs:label": "Software",
        },
        {
            "@id": "dcite:Supervision",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Supervision",
            "rdfs:label": "Supervision",
        },
        {
            "@id": "dcite:Validation",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Validation",
            "rdfs:label": "Validation",
        },
        {
            "@id": "dcite:Visualization",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Visualization",
            "rdfs:label": "Visualization",
        },
        {
            "@id": "dcite:Funder",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Funder",
            "rdfs:label": "Funder",
        },
        {
            "@id": "dcite:Sponsor",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Sponsor",
            "rdfs:label": "Sponsor",
        },
        {
            "@id": "dcite:StudyParticipant",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Participant in a study",
            "rdfs:label": "Study participant",
        },
        {
            "@id": "dcite:Affiliation",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Affiliated with an entity",
            "rdfs:label": "Affiliation",
        },
        {
            "@id": "dcite:EthicsApproval",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Approved ethics protocol",
            "rdfs:label": "Ethics approval",
        },
        {
            "@id": "dcite:Other",
            "@type": "dandi:RoleType",
            "rdfs:comment": "Other",
            "rdfs:label": "Other",
        },
    ]
}

AgeReferenceTypeDict = {
    "@graph": [
        {
            "@id": "dandi:AgeReferenceType",
            "@type": "rdfs:Class",
            "rdfs:comment": "An enumeration of age reference",
            "rdfs:label": "Age reference type",
            "rdfs:subClassOf": {"@id": "schema:Enumeration"},
        },
        {
            "@id": "dandi:BirthReference",
            "@type": "dandi:AgeReferenceType",
            "rdfs:comment": "Age since Birth",
            "rdfs:label": "BirthReference",
        },
        {
            "@id": "dandi:GestationalReference",
            "@type": "dandi:AgeReferenceType",
            "rdfs:comment": "Age of a pregnancy (https://en.wikipedia.org/wiki/Gestational_age)",
            "rdfs:label": "GestationalReference",
        },
    ]
}
