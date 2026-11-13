
package com.example;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.*;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

/** Structural JUnit test-class merger. Does not claim semantic deduplication. */
public final class JunitMerger {

    private static String normalized(Node node) {
        return node.toString().replaceAll("\\s+", " ").trim();
    }

    private static String memberKey(BodyDeclaration<?> member) {
        if (member.isMethodDeclaration()) {
            MethodDeclaration method = member.asMethodDeclaration();
            StringJoiner params = new StringJoiner(",");
            method.getParameters().forEach(
                p -> params.add(p.getType().toString())
            );
            return "method:" + method.getNameAsString() + "(" + params + ")";
        }

        if (member.isConstructorDeclaration()) {
            ConstructorDeclaration ctor = member.asConstructorDeclaration();
            StringJoiner params = new StringJoiner(",");
            ctor.getParameters().forEach(
                p -> params.add(p.getType().toString())
            );
            return "constructor:" + ctor.getNameAsString() + "(" + params + ")";
        }

        if (member.isFieldDeclaration()) {
            FieldDeclaration field = member.asFieldDeclaration();
            StringJoiner names = new StringJoiner(",");
            field.getVariables().forEach(
                v -> names.add(v.getNameAsString())
            );
            return "field:" + names;
        }

        if (member.isClassOrInterfaceDeclaration()) {
            return "type:" +
                member.asClassOrInterfaceDeclaration().getNameAsString();
        }

        return "other:" + normalized(member);
    }

    private static boolean isLifecycleMethod(MethodDeclaration method) {
    return method.getParameters().isEmpty()
        && method.getAnnotations().stream().anyMatch(annotation ->
            annotation.getNameAsString().equals("BeforeEach")
            || annotation.getNameAsString().equals("AfterEach")
        );
}


private static boolean isJUnitTestMethod(MethodDeclaration method) {
    return method.getAnnotations().stream()
        .anyMatch(annotation ->
            annotation.getName().getIdentifier().equals("Test")
        );
}

    private static String uniqueLifecycleName(
        ClassOrInterfaceDeclaration merged,
        String originalName) {

    String baseName = originalName + "BVA";
    String name = baseName;
    int suffix = 2;

    while (!merged.getMethodsByName(name).isEmpty()) {
        name = baseName + suffix++;
    }

    return name;
}

    public static void main(String[] args) throws Exception {

        if (args.length != 4) {
            System.err.println(
                "Usage: java -jar junit-merger.jar EP.java BV.java OUTPUT.java MergedClassName"
            );
            System.exit(2);
        }

        CompilationUnit ep = StaticJavaParser.parse(Path.of(args[0]));
        CompilationUnit bv = StaticJavaParser.parse(Path.of(args[1]));

        String epPackage = ep.getPackageDeclaration()
            .map(p -> p.getNameAsString()).orElse("");

        String bvPackage = bv.getPackageDeclaration()
            .map(p -> p.getNameAsString()).orElse("");

        if (!epPackage.equals(bvPackage)) {
            throw new IllegalArgumentException("Package mismatch");
        }

        ClassOrInterfaceDeclaration epClass = ep.getPrimaryType()
            .filter(TypeDeclaration::isClassOrInterfaceDeclaration)
            .orElseThrow(() ->
                new IllegalArgumentException("EP must contain a primary class")
            )
            .asClassOrInterfaceDeclaration();

        ClassOrInterfaceDeclaration bvClass = bv.getPrimaryType()
            .filter(TypeDeclaration::isClassOrInterfaceDeclaration)
            .orElseThrow(() ->
                new IllegalArgumentException("BVA must contain a primary class")
            )
            .asClassOrInterfaceDeclaration();

        CompilationUnit out = new CompilationUnit();

        if (!epPackage.isEmpty()) {
            out.setPackageDeclaration(epPackage);
        }

        Set<String> imports = new LinkedHashSet<>();

        for (CompilationUnit cu : List.of(ep, bv)) {
            for (ImportDeclaration imp : cu.getImports()) {
                if (imports.add(imp.toString().trim())) {
                    out.addImport(imp.clone());
                }
            }
        }

        ClassOrInterfaceDeclaration merged = out.addClass(args[3]);

        Set<String> seenBodies = new HashSet<>();
        Map<String, String> keyedMembers = new HashMap<>();

        for (ClassOrInterfaceDeclaration input : List.of(epClass, bvClass)) {

            for (BodyDeclaration<?> original : input.getMembers()) {

                BodyDeclaration<?> member = original.clone();

                String key = memberKey(member);
                String body = normalized(member);

                // Skip identical members.
                if (seenBodies.contains(body)) {
                    continue;
                }

                // Handle conflicting @BeforeEach setUp() methods.
                if (keyedMembers.containsKey(key)
                        && member.isMethodDeclaration()) {

                    MethodDeclaration method = member.asMethodDeclaration();

                    if (isLifecycleMethod(method) || isJUnitTestMethod(method)) {

                        String originalName = method.getNameAsString();

                        String newName = uniqueLifecycleName(
                            merged,
                            originalName
                        );

                        method.setName(newName);

                        key = memberKey(member);
                        body = normalized(member);

                        // System.out.println(
                        //     "Renamed conflicting " + originalName
                        //     + "() to " + newName + "()"
                        // );
                    }
                }

                // Reject other conflicting declarations.
                if (keyedMembers.containsKey(key)) {
                    throw new IllegalArgumentException(
                        "Conflicting member " + key +
                        ". Resolve the two generated versions before merging."
                    );
                }

                keyedMembers.put(key, body);
                seenBodies.add(body);
                merged.addMember(member);
            }
        }

        Path destination = Path.of(args[2]);

        if (destination.getParent() != null) {
            Files.createDirectories(destination.getParent());
        }

        Files.writeString(destination, out.toString());

        // System.out.println("Merged Java file: " + destination);
    }
}
